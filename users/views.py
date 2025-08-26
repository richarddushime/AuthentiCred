from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from blockchain.utils.crypto import generate_key_pair
from wallets.models import Wallet
from blockchain.tasks import process_did_registration_confirmation
from .forms import CustomUserCreationForm, CustomAuthenticationForm, EditProfileForm, ChangePasswordForm, DeleteAccountForm, InstitutionSettingsForm, ContactForm
from .models import InstitutionProfile
from blockchain.services import BlockchainService
from blockchain.models import DIDRegistration, OnChainTransaction
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'users/home.html')

@ensure_csrf_cookie
@csrf_protect
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
            login(request, user)

            if user.user_type == 'INSTITUTION':
                blockchain_service = BlockchainService()
                try:
                    # Register DID
                    tx_hash = blockchain_service.register_did(user.did, user.public_key)
                    messages.info(request, f"DID registration initiated. Transaction: {tx_hash[:10]}...")
                    
                    # Create institution profile
                    profile = InstitutionProfile.objects.create(user=user)
                    
                    # Create DID registration record
                    tx = OnChainTransaction.objects.get(tx_hash=tx_hash)
                    DIDRegistration.objects.create(
                        did=user.did,
                        public_key=user.public_key,
                        institution=profile,
                        transaction=tx
                    )
                    
                    # Schedule background check
                    process_did_registration_confirmation.delay()
                    
                except Exception as e:
                    logger.error(f"Blockchain operation failed: {str(e)}")
                    messages.error(request, "DID registration started, but trust status will be updated later.")
            
            return redirect('profile')
        else:
            logger.warning(f"Registration form errors: {form.errors}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('profile')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile_view(request):
    user = request.user
    context = {'user': user}
    
    # Add institution-specific data
    if user.user_type == 'INSTITUTION':
        try:
            profile = InstitutionProfile.objects.get(user=user)
            context['profile'] = profile
            
            # Use the new trust status method
            context['is_trusted'] = user.get_trust_status()
            
            # Get blockchain transactions
            context['transactions'] = OnChainTransaction.objects.filter(
                metadata__did=user.did
            ).order_by('-created_at')[:5]
            
        except InstitutionProfile.DoesNotExist:
            logger.warning(f"Institution profile missing for user: {user.id}")
            messages.warning(request, "Institution profile not completed. Please update your profile.")
    
    return render(request, 'users/profile.html', context)

@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}
    # trust status to context
    context['is_trusted'] = user.get_trust_status()
    # Simplified user type checks using Django model methods
    if user.is_issuer():
        # Issuer dashboard
        context['issued_credentials'] = user.issued_credentials.all()[:5]
        context['pending_actions'] = [
            {'title': 'Issue New Credential', 'url': reverse('issue_credential')},
        ]
    
    elif user.is_holder():
        # Holder dashboard
        context['my_credentials'] = user.credentials.all()[:5]
        context['pending_actions'] = [
            {'title': 'Add New Credential', 'url': '#'},
            {'title': 'Share Credentials', 'url': '#'},
        ]
    
    elif user.is_verifier():
        # Verifier dashboard
        context['recent_verifications'] = []
        context['pending_actions'] = [
            {'title': 'Verify Credentials', 'url': reverse('verify_credential')},
        ]
    
    return render(request, 'users/dashboard.html', context)

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = EditProfileForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    else:
        form = ChangePasswordForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            # Delete user account
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
    else:
        form = DeleteAccountForm(request.user)
    
    return render(request, 'users/delete_account.html', {'form': form})

@login_required
def institution_settings_view(request):
    if not request.user.is_issuer():
        messages.error(request, "Only institutions can access institution settings")
        return redirect('dashboard')
    
    try:
        profile = InstitutionProfile.objects.get(user=request.user)
    except InstitutionProfile.DoesNotExist:
        profile = InstitutionProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = InstitutionSettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Institution settings updated successfully!')
            return redirect('institution_settings')
    else:
        form = InstitutionSettingsForm(instance=profile)
    
    return render(request, 'users/institution_settings.html', {'form': form})

def about_view(request):
    return render(request, 'users/about.html')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Here you would typically send an email or save to database
            # For now, we'll just show a success message
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'users/contact.html', {'form': form})
