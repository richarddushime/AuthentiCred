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
from blockchain.utils.crypto import generate_key_pair
from wallets.models import Wallet
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if created:
        # Generate keys for new wallet
        private_key, public_key = generate_key_pair()
        wallet.private_key = private_key
        wallet.save()
        
        # Update user's public key
        request.user.public_key = public_key
        request.user.save()
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
    
    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'copy_link':
            # Link copy action (handled by JavaScript, but we can add server-side validation)
            messages.success(request, 'Share link copied to clipboard!')
            return JsonResponse({'status': 'success', 'message': 'Link copied successfully'})
            
        elif action == 'send_email':
            # Email sharing action
            recipient_email = request.POST.get('recipient_email')
            message = request.POST.get('message', '')
            
            if not recipient_email:
                messages.error(request, 'Please enter a valid email address')
            else:
                try:
                    # Here you would implement actual email sending
                    # For now, we'll just show a success message
                    share_url = request.build_absolute_uri(
                        reverse('view_shared_credential', args=[str(wallet_cred.id)]))
                    
                    # In a real implementation, you would send an email here
                    # send_credential_email(recipient_email, message, share_url, wallet_cred.credential)
                    
                    messages.success(request, f'Credential shared successfully with {recipient_email}!')
                except Exception as e:
                    messages.error(request, f'Failed to send credential: {str(e)}')
                    
        elif action == 'download_qr':
            # QR code download action
            messages.success(request, 'QR code downloaded successfully!')
            return JsonResponse({'status': 'success', 'message': 'QR code downloaded'})
    
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
    
    # Save QR code to in-memory buffer and convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    import base64
    qr_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    
    context = {
        'wallet_cred': wallet_cred,
        'credential': wallet_cred.credential,  # Add the credential object
        'share_url': share_url,
        'qr_img': qr_img,
    }
    return render(request, 'wallets/share_credential.html', context)

def view_shared_credential(request, credential_id):
    """Public view for shared credentials - no login required"""
    wallet_cred = get_object_or_404(WalletCredential, id=credential_id)
    credential = wallet_cred.credential
    
    # Check blockchain status
    blockchain_service = BlockchainService()
    is_anchored = False
    issuer_trusted = False
    is_revoked = False
    
    try:
        # Get VC hash with error handling
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
        
    except Exception as e:
        # If blockchain verification fails, continue without it
        messages.warning(request, 'Blockchain verification temporarily unavailable')
    
    return render(request, 'wallets/view_shared_credential.html', {
        'credential': credential,
        'is_anchored': is_anchored,
        'issuer_trusted': issuer_trusted,
        'is_revoked': is_revoked,
    })

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
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{credential.credential_type}_{credential.id}.pdf"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1f2937')
    )
    story.append(Paragraph("AuthentiCred - Verified Credential", title_style))
    story.append(Spacer(1, 20))
    
    # Credential Information
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.HexColor('#374151')
    )
    
    # Basic Information
    story.append(Paragraph(f"<b>Credential Type:</b> {credential.credential_type}", info_style))
    story.append(Paragraph(f"<b>Title:</b> {credential.title}", info_style))
    story.append(Paragraph(f"<b>Issued To:</b> {credential.holder.get_full_name() or credential.holder.username}", info_style))
    story.append(Paragraph(f"<b>Issued By:</b> {credential.issuer.get_full_name() or credential.issuer.username}", info_style))
    story.append(Paragraph(f"<b>Issue Date:</b> {credential.issued_at.strftime('%B %d, %Y')}", info_style))
    
    if credential.expiration_date:
        story.append(Paragraph(f"<b>Expiration Date:</b> {credential.expiration_date.strftime('%B %d, %Y')}", info_style))
    
    story.append(Spacer(1, 20))
    
    # Credential Details Table
    if credential.vc_json and 'credentialSubject' in credential.vc_json:
        story.append(Paragraph("<b>Credential Details:</b>", info_style))
        story.append(Spacer(1, 10))
        
        # Create table for credential details
        data = [['Field', 'Value']]
        subject = credential.vc_json['credentialSubject']
        
        for key, value in subject.items():
            if key != 'id':  # Skip the DID
                data.append([key.replace('_', ' ').title(), str(value)])
        
        if len(data) > 1:  # If we have data beyond the header
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ]))
            story.append(table)
    
    story.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6b7280')
    )
    story.append(Paragraph("This document was generated by AuthentiCred", footer_style))
    story.append(Paragraph(f"Credential ID: {credential.id}", footer_style))
    story.append(Paragraph(f"Generated on: {credential.issued_at.strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    
    # Build PDF
    doc.build(story)
    return response
