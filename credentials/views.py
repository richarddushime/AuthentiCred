# credentials/views.py
import hashlib
import re
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Credential, CredentialSchema
from .forms import CredentialSchemaForm, CredentialIssueForm, CredentialRevokeForm
from users.models import User
from blockchain.services import BlockchainService
from blockchain.utils.vc_proofs import sign_json_ld, verify_json_ld
from wallets.models import WalletCredential
from datetime import datetime, timedelta
from django.utils import timezone
from blockchain.utils.crypto import generate_key_pair
from wallets.models import Wallet
from blockchain.utils.vc_proofs import verify_json_ld_signature
from django import forms
import os
import ecdsa
from blockchain.utils.crypto import generate_public_key_from_private

class CredentialVerificationForm(forms.Form):
    """Form for submitting credential hash"""
    credential_hash = forms.CharField(
        label='Credential Hash',
        max_length=64,
        min_length=64,
        widget=forms.TextInput(attrs={'placeholder': 'Enter 64-character credential hash'}))
    
    def clean_credential_hash(self):
        hash = self.cleaned_data['credential_hash'].strip()
        if not all(c in '0123456789abcdef' for c in hash):
            raise forms.ValidationError("Invalid hash format. Must be hexadecimal.")
        return hash
@login_required

def verify_credential(request):
    """Public credential verification view"""
    if request.method == 'POST':
        form = CredentialVerificationForm(request.POST)
        if form.is_valid():
            vc_hash = form.cleaned_data['credential_hash']
            
            try:
                # Try to find credential in database
                credential = Credential.objects.get(vc_hash=vc_hash)
                return show_verification_result(request, credential)
                
            except Credential.DoesNotExist:
                # Credential not in database - attempt external verification
                return verify_external_credential(request, vc_hash)
                
    else:
        form = CredentialVerificationForm()
    
    return render(request, 'credentials/verify_credential.html', {'form': form})

def show_verification_result(request, credential):
    blockchain_service = BlockchainService()
    
    # 1. Verify cryptographic signature
    try:
        # Get the JWS signature from the proof
        jws = credential.vc_json['proof']['jws']
        signature_hex = jws.split('=')[1]  # Extract signature part from "v=<signature>"
        
        # Recreate the original VC without the proof
        vc_without_proof = {k: v for k, v in credential.vc_json.items() if k != 'proof'}
        vc_json_str = json.dumps(vc_without_proof, separators=(',', ':'), sort_keys=True)
        vc_bytes = vc_json_str.encode('utf-8')
        
        signature_valid = verify_json_ld(
            vc_bytes,
            signature_hex,
            credential.issuer.wallet.public_key
        )
    except Exception as e:
        signature_valid = False
        
    # 2. Check blockchain anchoring
    is_anchored = blockchain_service.verify_anchored(credential.vc_hash)
    
    # 3. Check revocation status - using credential ID as string
    try:
        is_revoked = blockchain_service.is_credential_revoked(str(credential.id))
    except Exception:
        is_revoked = None  # Indeterminate status
    
    # 4. Check issuer trust status
    issuer_trusted = blockchain_service.is_issuer_registered(credential.issuer.did)
    
    # 5. Check expiration
    is_expired = credential.expiration_date < timezone.now() if credential.expiration_date else False
    
    return render(request, 'credentials/verification_result.html', {
        'credential': credential,
        'signature_valid': signature_valid,
        'is_anchored': is_anchored,
        'is_revoked': is_revoked,
        'issuer_trusted': issuer_trusted,
        'is_expired': is_expired,
        'overall_valid': (
            signature_valid and 
            is_anchored and 
            (is_revoked is not True) and  # Not revoked or indeterminate
            issuer_trusted and 
            not is_expired
        ),
        'source': 'internal'
    })

def verify_external_credential(request, vc_hash):
    """Handle verification for credentials not in our database"""
    blockchain_service = BlockchainService()
    
    # 1. Check if anchored on blockchain
    is_anchored = blockchain_service.verify_anchored(vc_hash)
    
    # 2. For external credentials, we can't check revocation without the credential ID
    is_revoked = None  # Unknown for external credentials
    
    return render(request, 'credentials/verification_result.html', {
        'vc_hash': vc_hash,
        'is_anchored': is_anchored,
        'is_revoked': is_revoked,
        'overall_valid': is_anchored,  # Only anchoring can be verified
        'source': 'external'
    })

@login_required
def schema_list(request):
    if not request.user.is_issuer():
        messages.error(request, "Only institutions can manage schemas")
        return redirect('dashboard')
    
    schemas = CredentialSchema.objects.filter(created_by=request.user)
    return render(request, 'credentials/schema_list.html', {'schemas': schemas})

@login_required
def schema_create(request):
    if not request.user.is_issuer():
        messages.error(request, "Only institutions can create schemas")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CredentialSchemaForm(request.POST)
        if form.is_valid():
            schema = form.save(commit=False)
            schema.created_by = request.user
            try:
                # Validate JSON structure
                json.loads(json.dumps(schema.fields))
                schema.save()
                messages.success(request, 'Schema created successfully!')
                return redirect('schema_list')
            except json.JSONDecodeError:
                messages.error(request, 'Invalid JSON format for fields')
    else:
        form = CredentialSchemaForm()
    
    return render(request, 'credentials/schema_form.html', {
        'form': form,
        'title': 'Create New Schema'
    })

@login_required
def issue_credential(request, schema_id=None):
    if not request.user.is_issuer():
        messages.error(request, "Only institutions can issue credentials")
        return redirect('dashboard')
    
    schema = None
    if schema_id:
        schema = get_object_or_404(CredentialSchema, id=schema_id, created_by=request.user)
    
    if request.method == 'POST':
        form = CredentialIssueForm(request.POST, issuer=request.user, initial={'schema': schema})
        if form.is_valid():
            # Find holder by email
            holder_email = form.cleaned_data['holder_email']
            try:
                holder = User.objects.get(email=holder_email, user_type='STUDENT')
            except User.DoesNotExist:
                messages.error(request, 'Student with this email not found')
                return render(request, 'credentials/issue_credential.html', {'form': form, 'schema': schema})
            
            # Build credential subject
            subject_data = {"id": holder.did}  # Use holder's DID
            if schema and schema.fields:
                for field_name in schema.fields.keys():
                    subject_data[field_name] = form.cleaned_data.get(field_name, "")
            # Ensure issuer has a wallet
            if not hasattr(request.user, 'wallet'):
                from blockchain.utils.crypto import generate_key_pair
                private_key_hex, public_key_hex = generate_key_pair()
                
                Wallet.objects.create(user=request.user, private_key=private_key_hex)
                request.user.public_key = public_key_hex
                request.user.save()
                messages.info(request, "A wallet was created for your account")
            # Build Verifiable Credential
            vc = {
                "@context": ["https://www.w3.org/2018/credentials/v1"],
                "type": ["VerifiableCredential", schema.name if schema else "CustomCredential"],
                "issuer": request.user.did,
                "issuanceDate": datetime.utcnow().isoformat() + "Z",
                "credentialSubject": subject_data,
            }
            
            # Sign the credential
            try:
                wallet = request.user.wallet
                private_key = wallet.private_key
                
                # Handle different private key formats
                if len(private_key) == 44:  # Base64 encoded (32 bytes)
                    # Convert base64 to hex
                    import base64
                    private_key_bytes = base64.b64decode(private_key)
                    private_key_hex = private_key_bytes.hex()
                else:
                    # Assume hex format, clean it
                    private_key_hex = re.sub(r'[^0-9a-fA-F]', '', private_key)
                    if private_key_hex.startswith('0x'):
                        private_key_hex = private_key_hex[2:]
                
                if len(private_key_hex) != 64:
                    # If still not 64 chars, regenerate the wallet with proper keys
                    from blockchain.utils.crypto import generate_key_pair
                    new_private_key_hex, new_public_key_hex = generate_key_pair()
                    
                    # Update the wallet
                    wallet.private_key = new_private_key_hex
                    wallet.save()
                    
                    # Update user's public key
                    request.user.public_key = new_public_key_hex
                    request.user.save()
                    
                    private_key_hex = new_private_key_hex
                    messages.info(request, "Wallet keys were regenerated to fix compatibility issues")
                
                vc_json_str = json.dumps(vc, separators=(',', ':'), sort_keys=True)
                vc_bytes = vc_json_str.encode('utf-8')
                
                # Use the new sign_data function
                from blockchain.utils.crypto import sign_data
                signature_hex = sign_data(vc_bytes, private_key_hex)
                
                # Format as JWS (simplified version)
                jws = f"v={signature_hex}"
            except Exception as e:
                messages.error(request, f"Failed to sign credential: {str(e)}")
                return render(request, 'credentials/issue_credential.html', {'form': form, 'schema': schema})
            
            # Create credential instance with proof
            credential = Credential.objects.create(
                vc_json={
                    **vc,
                    "proof": {
                        "type": "EcdsaSecp256k1Signature2019",
                        "created": datetime.utcnow().isoformat() + "Z",
                        "proofPurpose": "assertionMethod",
                        "verificationMethod": f"{request.user.did}#keys-1",
                        "jws": jws
                    }
                },
                issuer=request.user,
                holder=holder,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                credential_type=schema.name if schema else "Custom Credential",
                expiration_date=form.cleaned_data['expiration_date'],
                schema=schema,
            )
            
            # Issue the credential
            if credential.issue():
                # Add to holder's wallet
                WalletCredential.objects.create(
                    wallet=holder.wallet,
                    credential=credential
                )
                
                # Anchor to blockchain
                try:
                    blockchain_service = BlockchainService()
                    tx_hash = blockchain_service.anchor_credential(credential.vc_hash)
                    messages.info(request, f"Credential anchored to blockchain. Transaction: {tx_hash[:10]}...")
                except Exception as e:
                    messages.warning(request, f"Credential issued but blockchain anchoring failed: {str(e)}")
                
                messages.success(request, 'Credential issued successfully!')
                return redirect('issued_credentials')
            else:
                messages.error(request, 'Failed to issue credential')
        else:
            messages.error(request, 'Please correct the errors below')
    else:
        initial = {'expiration_date': timezone.now() + timedelta(days=365)}
        form = CredentialIssueForm(initial=initial, issuer=request.user)
    
    return render(request, 'credentials/issue_credential.html', {
        'form': form,
        'schema': schema
    })

def verify_data(data: bytes, signature_hex: str, public_key_hex: str) -> bool:
    """Verify ECDSA signature"""
    vk = ecdsa.VerifyingKey.from_string(
        bytes.fromhex(public_key_hex),
        curve=ecdsa.SECP256k1
    )
    try:
        return vk.verify(bytes.fromhex(signature_hex), data, hashfunc=hashlib.sha256)
    except ecdsa.BadSignatureError:
        return False

@login_required
def issued_credentials(request):
    if not request.user.is_issuer():
        messages.error(request, "Only institutions can view issued credentials")
        return redirect('dashboard')
    
    credentials = Credential.objects.filter(issuer=request.user).order_by('-issued_at')
    return render(request, 'credentials/issued_credentials.html', {'credentials': credentials})

@login_required
def revoke_credential(request, credential_id):
    credential = get_object_or_404(Credential, id=credential_id, issuer=request.user)
    
    if request.method == 'POST':
        form = CredentialRevokeForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            if credential.revoke(reason=reason):
                # Revoke on blockchain
                try:
                    blockchain_service = BlockchainService()
                    # tx_hash = blockchain_service.revoke_credential(str(credential.id))
                    tx_hash = blockchain_service.revoke_credential(credential.id)

                    messages.info(request, f"Revocation recorded on blockchain. Transaction: {tx_hash[:10]}...")
                except Exception as e:
                    messages.warning(request, f"Credential revoked but blockchain update failed: {str(e)}")
                
                messages.success(request, 'Credential revoked successfully')
                return redirect('issued_credentials')
            else:
                messages.error(request, 'Failed to revoke credential')
    else:
        form = CredentialRevokeForm()
    
    return render(request, 'credentials/revoke_credential.html', {
        'form': form,
        'credential': credential
    })

@login_required
def credential_detail(request, credential_id):
    credential = get_object_or_404(Credential, id=credential_id)
    
    # Check if user has permission
    if not (request.user == credential.issuer or request.user == credential.holder):
        messages.error(request, "You don't have permission to view this credential")
        return redirect('dashboard')
    
    # Initialize blockchain status variables
    is_anchored = False
    issuer_trusted = False
    is_revoked = False
    
    try:
        # Check blockchain status
        blockchain_service = BlockchainService()
        
        # Get VC hash with error handling
        try:
            vc_hash = credential.vc_hash
        except (ValueError, AttributeError) as e:
            messages.error(request, f"Error computing credential hash: {str(e)}")
            vc_hash = None
        
        if vc_hash:
            is_anchored = blockchain_service.client.call_contract_function(
                'CredentialAnchor',
                'verifyProof',
                vc_hash
            )
        
        # Check issuer trust status
        issuer_trusted = blockchain_service.is_issuer_registered(credential.issuer.did)
        
        # Check revocation status
        is_revoked = blockchain_service.is_credential_revoked(str(credential.id))
        
    except Exception as e:
        messages.warning(request, f"Blockchain verification failed: {str(e)}")
    
    return render(request, 'credentials/credential_detail.html', {
        'credential': credential,
        'is_anchored': is_anchored,
        'issuer_trusted': issuer_trusted,
        'is_revoked': is_revoked,
    })

@login_required
def edit_credential(request, credential_id):
    """Edit a credential - only allowed for draft credentials"""
    credential = get_object_or_404(Credential, id=credential_id, issuer=request.user)
    
    # Only allow editing of draft credentials
    if credential.status != 'DRAFT':
        messages.error(request, "Only draft credentials can be edited")
        return redirect('credential_detail', credential_id=credential.id)
    
    if request.method == 'POST':
        form = CredentialIssueForm(request.POST, issuer=request.user, instance=credential)
        if form.is_valid():
            # Update credential fields
            credential.title = form.cleaned_data['title']
            credential.description = form.cleaned_data['description']
            credential.expiration_date = form.cleaned_data['expiration_date']
            
            # Update credential subject data if schema fields changed
            if credential.schema and credential.schema.fields:
                subject_data = {"id": credential.holder.did}
                for field_name in credential.schema.fields.keys():
                    subject_data[field_name] = form.cleaned_data.get(field_name, "")
                
                # Update the VC JSON
                credential.vc_json['credentialSubject'] = subject_data
                
                # Re-sign the credential with updated data
                try:
                    wallet = request.user.wallet
                    private_key = wallet.private_key
                    
                    # Handle different private key formats
                    if len(private_key) == 44:  # Base64 encoded
                        import base64
                        private_key_bytes = base64.b64decode(private_key)
                        private_key_hex = private_key_bytes.hex()
                    else:
                        private_key_hex = re.sub(r'[^0-9a-fA-F]', '', private_key)
                        if private_key_hex.startswith('0x'):
                            private_key_hex = private_key_hex[2:]
                    
                    if len(private_key_hex) != 64:
                        from blockchain.utils.crypto import generate_key_pair
                        new_private_key_hex, new_public_key_hex = generate_key_pair()
                        wallet.private_key = new_private_key_hex
                        wallet.save()
                        request.user.public_key = new_public_key_hex
                        request.user.save()
                        private_key_hex = new_private_key_hex
                    
                    # Create new VC without proof for signing
                    vc_without_proof = {k: v for k, v in credential.vc_json.items() if k != 'proof'}
                    vc_json_str = json.dumps(vc_without_proof, separators=(',', ':'), sort_keys=True)
                    vc_bytes = vc_json_str.encode('utf-8')
                    
                    # Sign the updated credential
                    from blockchain.utils.crypto import sign_data
                    signature_hex = sign_data(vc_bytes, private_key_hex)
                    
                    # Update the proof
                    jws = f"v={signature_hex}"
                    credential.vc_json['proof']['jws'] = jws
                    credential.vc_json['proof']['created'] = datetime.utcnow().isoformat() + "Z"
                    
                except Exception as e:
                    messages.error(request, f"Failed to re-sign credential: {str(e)}")
                    return render(request, 'credentials/edit_credential.html', {
                        'form': form,
                        'credential': credential
                    })
            
            credential.save()
            messages.success(request, 'Credential updated successfully!')
            return redirect('credential_detail', credential_id=credential.id)
        else:
            messages.error(request, 'Please correct the errors below')
    else:
        # Pre-populate form with existing data
        initial_data = {
            'title': credential.title,
            'description': credential.description,
            'expiration_date': credential.expiration_date,
            'holder_email': credential.holder.email,
        }
        
        # Add schema field values
        if credential.schema and credential.schema.fields:
            subject_data = credential.vc_json.get('credentialSubject', {})
            for field_name in credential.schema.fields.keys():
                if field_name in subject_data:
                    initial_data[field_name] = subject_data[field_name]
        
        form = CredentialIssueForm(initial=initial_data, issuer=request.user)
    
    return render(request, 'credentials/edit_credential.html', {
        'form': form,
        'credential': credential
    })
