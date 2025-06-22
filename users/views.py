# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import InstitutionProfile
from blockchain.services import BlockchainService
from blockchain.models import OnChainTransaction

def home(request):
    return render(request, 'users/home.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # For institutions, start DID registration process
            if user.user_type == 'INSTITUTION':
                blockchain_service = BlockchainService()
                try:
                    # Register DID on blockchain
                    tx_hash = blockchain_service.register_did(user.did, user.public_key)
                    messages.info(request, f"DID registration initiated. Transaction: {tx_hash[:10]}...")
                    
                    # Set institution as trusted (in this demo, we auto-approve)
                    profile = user.institution_profile
                    profile.is_trusted = True
                    profile.save()
                    
                    # Update trust status on blockchain
                    tx_trust = blockchain_service.client.execute_contract_function(
                        'TrustRegistry',
                        'setIssuerTrustStatus',
                        user.did,
                        True
                    )
                    messages.info(request, f"Institution trust status updated. Transaction: {tx_trust[:10]}...")
                    
                except Exception as e:
                    messages.error(request, f"Blockchain operation failed: {str(e)}")
            
            messages.success(request, 'Registration successful!')
            return redirect('profile')
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
            
            # Check blockchain status
            blockchain_service = BlockchainService()
            context['is_trusted'] = blockchain_service.is_issuer_registered(user.did)
            
            # Get blockchain transactions
            context['transactions'] = OnChainTransaction.objects.filter(
                metadata__did=user.did
            ).order_by('-created_at')[:5]
            
        except InstitutionProfile.DoesNotExist:
            pass
    
    return render(request, 'users/profile.html', context)

@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}
    
    if user.is_issuer():
        # Issuer dashboard
        context['issued_credentials'] = user.issued_credentials.all()[:5]
        context['pending_actions'] = [
            {'title': 'Verify Accreditation', 'url': '#'},
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
            {'title': 'Request Credentials', 'url': '#'},
        ]
    
    return render(request, 'users/dashboard.html', context)
