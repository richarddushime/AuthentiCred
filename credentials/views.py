# credentials/views.py
import hashlib
import re
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Credential, CredentialSchema, VerificationRecord
from .forms import CredentialSchemaForm, CredentialIssueForm, CredentialRevokeForm
from users.models import User
from blockchain.services import BlockchainService
from blockchain.tasks import anchor_credential_task, revoke_credential_task
from blockchain.utils.task_runner import execute_task_with_fallback, get_task_status_message
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

def verify_credential(request):
    """Public credential verification view"""
    if request.method == 'POST':
        form = CredentialVerificationForm(request.POST)
        if form.is_valid():
            vc_hash = form.cleaned_data['credential_hash']
            
            # Try to find credential in database by hash
            try:
                credential = Credential.objects.get(vc_hash=vc_hash)
                print(f"Found credential in database: {credential.id} with status: {credential.status}")
                return show_verification_result(request, credential)
            except Credential.DoesNotExist:
                print(f"Credential not found in database for hash: {vc_hash}")
                # Credential not in database - attempt external verification
                return verify_external_credential(request, vc_hash)
            except Exception as e:
                print(f"Error during credential lookup: {e}")
                import traceback
                traceback.print_exc()
                # If there's an error, fall back to external verification
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
        
        # Use the verify_data function that matches the sign_data function used for signing
        signature_valid = verify_data(
            vc_bytes,
            signature_hex,
            credential.issuer.public_key
        )
        
    except Exception as e:
        signature_valid = False
        
    # 2. Check blockchain anchoring
    try:
        is_anchored = blockchain_service.client.call_contract_function(
            'CredentialAnchor',
            'verifyProof',
            credential.vc_hash
        )
    except Exception as e:
        is_anchored = False
    
    # 3. Check revocation status - using credential ID as string
    try:
        is_revoked = blockchain_service.is_credential_revoked(str(credential.id))
    except Exception:
        # For internal credentials, we can check the database status
        is_revoked = credential.status == 'REVOKED'
    
    # 4. Check issuer trust status
    try:
        issuer_trusted = blockchain_service.is_issuer_registered(credential.issuer.did)
    except Exception:
        # For internal credentials, assume issuer is trusted if they have a DID
        issuer_trusted = bool(credential.issuer.did)
    
    # 5. Check expiration
    is_expired = credential.expiration_date < timezone.now().date() if credential.expiration_date else False
    
    # 6. Check issued status
    is_issued = credential.status == 'ISSUED'
    
    # 7. Check document integrity
    document_integrity_valid = credential.verify_document_integrity()
    
    overall_valid = (
        signature_valid and 
        is_anchored and 
        (is_revoked is not True) and  # Not revoked or indeterminate
        issuer_trusted and 
        not is_expired and
        is_issued and
        document_integrity_valid
    )
    
    # Create verification record if user is logged in
    if request.user.is_authenticated:
        VerificationRecord.objects.create(
            verifier=request.user,
            credential_hash=credential.vc_hash,
            credential=credential,
            is_valid=overall_valid,
            verification_details={
                'signature_valid': signature_valid,
                'is_anchored': is_anchored,
                'is_revoked': is_revoked,
                'issuer_trusted': issuer_trusted,
                'is_expired': is_expired,
                'is_issued': is_issued,
                'document_integrity_valid': document_integrity_valid,
                'overall_valid': overall_valid
            },
            source='INTERNAL'
        )
    
    return render(request, 'credentials/verification_result.html', {
        'credential': credential,
        'signature_valid': signature_valid,
        'is_anchored': is_anchored,
        'is_revoked': is_revoked,
        'issuer_trusted': issuer_trusted,
        'is_expired': is_expired,
        'is_issued': is_issued,
        'document_integrity_valid': document_integrity_valid,
        'overall_valid': overall_valid,
        'source': 'internal'
    })

def verify_external_credential(request, vc_hash):
    """Handle verification for credentials not in our database"""
    blockchain_service = BlockchainService()
    
    # 1. Check if anchored on blockchain
    try:
        is_anchored = blockchain_service.client.call_contract_function(
            'CredentialAnchor',
            'verifyProof',
            vc_hash
        )
    except Exception as e:
        is_anchored = False
    
    # 2. For external credentials, we can't check revocation without the credential ID
    is_revoked = None  # Unknown for external credentials
    
    # 3. For external credentials, we can't check issued status
    is_issued = None  # Unknown for external credentials
    
    overall_valid = is_anchored  # Only anchoring can be verified
    
    # Create verification record if user is logged in
    if request.user.is_authenticated:
        VerificationRecord.objects.create(
            verifier=request.user,
            credential_hash=vc_hash,
            credential=None,  # External credential
            is_valid=overall_valid,
            verification_details={
                'is_anchored': is_anchored,
                'is_revoked': is_revoked,
                'is_issued': is_issued,
                'overall_valid': overall_valid
            },
            source='EXTERNAL'
        )
    
    return render(request, 'credentials/verification_result.html', {
        'vc_hash': vc_hash,
        'is_anchored': is_anchored,
        'is_revoked': is_revoked,
        'is_issued': is_issued,
        'overall_valid': overall_valid,
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
        form = CredentialIssueForm(request.POST, request.FILES, issuer=request.user, initial={'schema': schema})
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
            
            # Add document hash to credential subject if document is uploaded
            if form.cleaned_data.get('document'):
                import hashlib
                document = form.cleaned_data['document']
                document.seek(0)  # Reset file pointer to beginning
                document_hash = hashlib.sha256(document.read()).hexdigest()
                vc['credentialSubject']['documentHash'] = document_hash
                vc['credentialSubject']['documentFilename'] = document.name
                document.seek(0)  # Reset file pointer for saving
            
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
                credential_type=schema.name if schema else "Credential",
                expiration_date=form.cleaned_data['expiration_date'],
                schema=schema,
                document=form.cleaned_data.get('document'),
            )
            
            # Check if user wants to save as draft or issue immediately
            action = request.POST.get('action', 'issue')
            
            if action == 'draft':
                # Save as draft
                messages.success(request, 'Credential saved as draft!')
                return redirect('issued_credentials')
            else:
                # Issue the credential
                if credential.issue():
                    # Add to holder's wallet
                    WalletCredential.objects.create(
                        wallet=holder.wallet,
                        credential=credential
                    )
                    
                    # Anchor to blockchain using fallback mechanism (Celery first, then direct execution)
                    try:
                        task_result = execute_task_with_fallback(anchor_credential_task, credential.vc_hash)
                        status_message = get_task_status_message(task_result)
                        if task_result['success']:
                            messages.info(request, status_message)
                        else:
                            messages.warning(request, status_message)
                    except Exception as e:
                        messages.warning(request, f"Credential issued but anchoring failed: {str(e)}")
                    
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
                # Revoke on blockchain using fallback mechanism (Celery first, then direct execution)
                try:
                    task_result = execute_task_with_fallback(revoke_credential_task, str(credential.id))
                    status_message = get_task_status_message(task_result)
                    if task_result['success']:
                        messages.info(request, status_message)
                    else:
                        messages.warning(request, status_message)
                except Exception as e:
                    messages.warning(request, f"Credential revoked but revocation failed: {str(e)}")
                
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
    # Try to find Credential by ID first
    credential = Credential.objects.filter(id=credential_id).first()
    
    # If not found, try to find by WalletCredential ID
    if not credential:
        from wallets.models import WalletCredential
        try:
            wallet_cred = WalletCredential.objects.get(id=credential_id, wallet__user=request.user)
            credential = wallet_cred.credential
        except WalletCredential.DoesNotExist:
            from django.http import Http404
            raise Http404("No Credential matches the given query.")
    
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
            try:
                is_anchored = blockchain_service.client.call_contract_function(
                    'CredentialAnchor',
                    'verifyProof',
                    vc_hash
                )
            except Exception as e:
                messages.warning(request, f"Failed to check credential anchoring: {str(e)}")
                is_anchored = False
        
        # Check issuer trust status
        try:
            issuer_trusted = blockchain_service.is_issuer_registered(credential.issuer.did)
        except Exception as e:
            messages.warning(request, f"Failed to check issuer trust status: {str(e)}")
            issuer_trusted = False
        
        # Check revocation status
        try:
            is_revoked = blockchain_service.is_credential_revoked(str(credential.id))
        except Exception as e:
            messages.warning(request, f"Failed to check revocation status: {str(e)}")
            is_revoked = False
        
    except Exception as e:
        messages.warning(request, f"Blockchain verification failed: {str(e)}")
        # Set default values if blockchain service is unavailable
        is_anchored = False
        issuer_trusted = False
        is_revoked = False
    
    return render(request, 'credentials/credential_detail.html', {
        'credential': credential,
        'is_anchored': is_anchored,
        'issuer_trusted': issuer_trusted,
        'is_revoked': is_revoked,
    })

@login_required
def edit_credential(request, credential_id):
    """Edit a credential - allowed for draft and issued credentials"""
    credential = get_object_or_404(Credential, id=credential_id, issuer=request.user)
    
    # Allow editing of draft and issued credentials
    if credential.status not in ['DRAFT', 'ISSUED']:
        messages.error(request, "Only draft and issued credentials can be edited")
        return redirect('credential_detail', credential_id=credential.id)
    
    if request.method == 'POST':
        form = CredentialIssueForm(request.POST, request.FILES, issuer=request.user, instance=credential)
        if form.is_valid():
            # Update credential fields
            credential.title = form.cleaned_data['title']
            credential.description = form.cleaned_data['description']
            credential.expiration_date = form.cleaned_data['expiration_date']
            
            # Update document if a new one is uploaded
            if form.cleaned_data.get('document'):
                credential.document = form.cleaned_data['document']
                
                # Update document hash in credential subject
                import hashlib
                document = form.cleaned_data['document']
                document.seek(0)  # Reset file pointer to beginning
                document_hash = hashlib.sha256(document.read()).hexdigest()
                credential.vc_json['credentialSubject']['documentHash'] = document_hash
                credential.vc_json['credentialSubject']['documentFilename'] = document.name
                document.seek(0)  # Reset file pointer for saving
            
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
            'document': credential.document,
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

@login_required
def issue_draft_credential(request, credential_id):
    """Issue a draft credential"""
    credential = get_object_or_404(Credential, id=credential_id, issuer=request.user)
    
    # Only allow issuing of draft credentials
    if credential.status != 'DRAFT':
        messages.error(request, "Only draft credentials can be issued")
        return redirect('credential_detail', credential_id=credential.id)
    
    if request.method == 'POST':
        try:
            # Issue the credential
            if credential.issue():
                # Add to holder's wallet
                WalletCredential.objects.create(
                    wallet=credential.holder.wallet,
                    credential=credential
                )
                
                # Anchor to blockchain using fallback mechanism (Celery first, then direct execution)
                try:
                    task_result = execute_task_with_fallback(anchor_credential_task, credential.vc_hash)
                    status_message = get_task_status_message(task_result)
                    if task_result['success']:
                        messages.info(request, status_message)
                    else:
                        messages.warning(request, status_message)
                except Exception as e:
                    messages.warning(request, f"Credential issued but anchoring failed: {str(e)}")
                
                messages.success(request, 'Credential issued successfully!')
                return redirect('issued_credentials')
            else:
                messages.error(request, 'Failed to issue credential')
        except Exception as e:
            messages.error(request, f'Error issuing credential: {str(e)}')
    
    return redirect('issued_credentials')

@login_required
def request_credential(request):
    """Request a credential from an issuer"""
    if not request.user.is_holder():
        messages.error(request, "Only students can request credentials")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Handle credential request form submission
        issuer_email = request.POST.get('issuer_email')
        credential_type = request.POST.get('credential_type')
        reason = request.POST.get('reason', '')
        
        if not issuer_email or not credential_type:
            messages.error(request, 'Please fill in all required fields')
        else:
            try:
                # Here you would implement the actual credential request logic
                # For now, we'll just show a success message
                messages.success(request, f'Credential request sent to {issuer_email}')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Failed to send request: {str(e)}')
    
    # Get available credential types from schemas
    available_types = CredentialSchema.objects.values_list('name', flat=True).distinct()
    
    return render(request, 'credentials/request_credential.html', {
        'available_types': available_types
    })

@login_required
def verification_history(request):
    """View verification history for verifiers"""
    if not request.user.is_verifier():
        messages.error(request, "Only verifiers can access verification history")
        return redirect('dashboard')
    
    # Get verification records for the current user
    verifications = VerificationRecord.objects.filter(verifier=request.user).select_related('credential', 'credential__issuer', 'credential__holder').order_by('-verification_date')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(verifications, 10)  # Show 10 verifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_verifications = verifications.count()
    valid_verifications = verifications.filter(is_valid=True).count()
    invalid_verifications = verifications.filter(is_valid=False).count()
    success_rate = (valid_verifications / total_verifications * 100) if total_verifications > 0 else 0
    
    return render(request, 'credentials/verification_history.html', {
        'page_obj': page_obj,
        'verifications': page_obj,
        'total_verifications': total_verifications,
        'valid_verifications': valid_verifications,
        'invalid_verifications': invalid_verifications,
        'success_rate': round(success_rate, 1)
    })

@login_required
def delete_verification(request, verification_id):
    """Delete a verification record"""
    if not request.user.is_verifier():
        messages.error(request, "Only verifiers can delete verification records")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            verification = VerificationRecord.objects.get(
                id=verification_id, 
                verifier=request.user
            )
            verification.delete()
            messages.success(request, 'Verification record deleted successfully!')
        except VerificationRecord.DoesNotExist:
            messages.error(request, 'Verification record not found or you do not have permission to delete it.')
        except Exception as e:
            messages.error(request, f'Error deleting verification record: {str(e)}')
    
    return redirect('verification_history')

@login_required
def shared_credentials(request):
    """View shared credentials for verifiers"""
    if not request.user.is_verifier():
        messages.error(request, "Only verifiers can access shared credentials")
        return redirect('dashboard')
    
    # Get shared credentials (WalletCredentials that are shared)
    from wallets.models import WalletCredential
    shared_credentials = WalletCredential.objects.filter(
        is_archived=False
    ).select_related('credential', 'credential__issuer', 'credential__holder').order_by('-added_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(shared_credentials, 10)  # Show 10 shared credentials per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'credentials/shared_credentials.html', {
        'page_obj': page_obj,
        'shared_credentials': page_obj,
        'total_shared': shared_credentials.count(),
    })
