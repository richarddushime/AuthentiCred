# wallets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib import messages
from .models import Wallet, WalletCredential
from credentials.models import Credential
from blockchain.services import BlockchainService
from blockchain.utils.vc_proofs import compute_sha256
import qrcode
from users.forms import CustomUserCreationForm
import json
from io import BytesIO
from wallets.utils import generate_key_pair
from wallets.models import Wallet

@login_required
def add_credential_to_wallet(request, credential_id):
    credential = get_object_or_404(Credential, id=credential_id, holder=request.user)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Check if credential already in wallet
    if WalletCredential.objects.filter(wallet=wallet, credential=credential).exists():
        messages.warning(request, 'This credential is already in your wallet')
    else:
        WalletCredential.objects.create(wallet=wallet, credential=credential)
        messages.success(request, 'Credential added to your wallet successfully')
    
    return redirect('credential_detail', credential_id=credential_id)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Create wallet with private key
            private_key, public_key = generate_key_pair()
            Wallet.objects.create(user=user, private_key=private_key)
            
            # Store public key on user
            user.public_key = public_key
            user.save()

@login_required
def wallet_home(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get all credentials in the wallet
    credentials = wallet.wallet_credentials.filter(is_archived=False).select_related('credential')
    
    # Categorize credentials
    credential_types = {}
    for wc in credentials:
        cred_type = wc.credential.credential_type
        if cred_type not in credential_types:
            credential_types[cred_type] = []
        credential_types[cred_type].append(wc)
    
    context = {
        'wallet': wallet,
        'credential_types': credential_types,
        'total_credentials': credentials.count(),
    }
    return render(request, 'wallets/wallet_home.html', context)

@login_required
def credential_detail(request, credential_id):
    wallet_cred = get_object_or_404(
        WalletCredential, 
        id=credential_id, 
        wallet__user=request.user,
        is_archived=False
    )
    credential = wallet_cred.credential
    
    # Check blockchain status
    blockchain_service = BlockchainService()
    vc_hash = compute_sha256(json.dumps(credential.vc_json))
    is_anchored = blockchain_service.client.call_contract_function(
        'CredentialAnchor',
        'verifyProof',
        vc_hash
    )
    
    # Check issuer trust status
    issuer_trusted = blockchain_service.is_issuer_registered(credential.issuer.did)
    
    # Check revocation status
    is_revoked = blockchain_service.is_credential_revoked(str(credential.id))
    
    context = {
        'wallet_cred': wallet_cred,
        'credential': credential,
        'is_anchored': is_anchored,
        'issuer_trusted': issuer_trusted,
        'is_revoked': is_revoked,
    }
    return render(request, 'wallets/credential_detail.html', context)


@login_required
def share_credential(request, credential_id):
    wallet_cred = get_object_or_404(
        WalletCredential, 
        id=credential_id, 
        wallet__user=request.user,
        is_archived=False
    )
    
    # Create a shareable link
    share_url = request.build_absolute_uri(
        reverse('view_shared_credential', args=[str(wallet_cred.id)]))
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(share_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to in-memory buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_img = buffer.getvalue()
    buffer.close()
    
    context = {
        'wallet_cred': wallet_cred,
        'share_url': share_url,
        'qr_img': qr_img,
    }
    return render(request, 'wallets/share_credential.html', context)

@login_required
def view_shared_credential(request, credential_id):
    wallet_cred = get_object_or_404(WalletCredential, id=credential_id)
    return credential_detail(request, wallet_cred.credential.id)

@login_required
def archive_credential(request, credential_id):
    wallet_cred = get_object_or_404(
        WalletCredential, 
        id=credential_id, 
        wallet__user=request.user
    )
    wallet_cred.is_archived = True
    wallet_cred.save()
    messages.success(request, 'Credential archived successfully')
    return redirect('wallet_home')

@login_required
def unarchive_credential(request, credential_id):
    wallet_cred = get_object_or_404(
        WalletCredential, 
        id=credential_id, 
        wallet__user=request.user
    )
    wallet_cred.is_archived = False
    wallet_cred.save()
    messages.success(request, 'Credential restored successfully')
    return redirect('wallet_home')

@login_required
def download_credential(request, credential_id):
    wallet_cred = get_object_or_404(
        WalletCredential, 
        id=credential_id, 
        wallet__user=request.user,
        is_archived=False
    )
    credential = wallet_cred.credential
    
    # Create a PDF representation
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{credential.credential_type}.pdf"'
    
    # Simplified PDF content
    pdf_content = f"""
    AuthentiCred - Verified Credential
    ==================================
    
    Credential Type: {credential.credential_type}
    Issued To: {credential.holder.username}
    Issued By: {credential.issuer.username}
    Issue Date: {credential.created_at.date()}
    
    Credential Details:
    {json.dumps(credential.vc_json, indent=2)}
    """
    
    response.write(pdf_content)

    return response
