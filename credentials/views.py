# credentials/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Credential, CredentialSchema
from .forms import CredentialSchemaForm, CredentialIssueForm, CredentialRevokeForm
from users.models import User
from blockchain.services import BlockchainService
from blockchain.utils.vc_proofs import sign_json_ld
from wallets.models import WalletCredential
from datetime import datetime, timedelta
from django.utils import timezone

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
            subject_data = {"id": f"did:authenticred:{holder.id}"}
            if schema and schema.fields:
                for field_name in schema.fields.keys():
                    subject_data[field_name] = form.cleaned_data.get(field_name, "")
            
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
                signed_vc = sign_json_ld(vc, wallet.private_key)
            except Exception as e:
                messages.error(request, f"Failed to sign credential: {str(e)}")
                return render(request, 'credentials/issue_credential.html', {'form': form, 'schema': schema})
            
            # Create credential instance
            credential = Credential.objects.create(
                vc_json=signed_vc,
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
                    tx_hash = blockchain_service.revoke_credential(str(credential.id))
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
    
    # Check blockchain status
    blockchain_service = BlockchainService()
    vc_hash = credential.vc_hash
    is_anchored = blockchain_service.client.call_contract_function(
        'CredentialAnchor',
        'verifyProof',
        vc_hash
    )
    
    # Check issuer trust status
    issuer_trusted = blockchain_service.is_issuer_registered(credential.issuer.did)
    
    # Check revocation status
    is_revoked = blockchain_service.is_credential_revoked(str(credential.id))
    
    return render(request, 'credentials/credential_detail.html', {
        'credential': credential,
        'is_anchored': is_anchored,
        'issuer_trusted': issuer_trusted,
        'is_revoked': is_revoked,
    })
