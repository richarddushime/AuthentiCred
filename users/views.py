from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages

from blockchain.tasks import process_did_registration_confirmation
from .forms import CustomUserCreationForm, CustomAuthenticationForm
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
