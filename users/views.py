from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Count, Q
from .forms import CustomUserCreationForm, CustomAuthenticationForm, EditProfileForm, ChangePasswordForm, DeleteAccountForm, InstitutionSettingsForm, ContactForm
from .models import User, InstitutionProfile
from credentials.models import Credential, VerificationRecord
from blockchain.models import DIDRegistration, OnChainTransaction
from blockchain.tasks import register_did_task, process_did_registration_confirmation
from blockchain.utils.task_runner import execute_task_with_fallback, get_task_status_message
from django.utils import timezone
from datetime import timedelta
from blockchain.utils.crypto import generate_key_pair
from blockchain.services import BlockchainService
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
            try:
                user = form.save()
                # Create wallet with private key
                private_key, public_key = generate_key_pair()
                # Assuming Wallet model exists and is imported
                # from wallets.models import Wallet
                # Wallet.objects.create(user=user, private_key=private_key)
                
                # Store public key on user
                user.public_key = public_key
                user.save()
                login(request, user)

                if user.user_type == 'INSTITUTION':
                    try:
                        # Create institution profile first
                        profile = InstitutionProfile.objects.create(user=user)
                        
                        # Register DID using fallback mechanism (Celery first, then direct execution)
                        task_result = execute_task_with_fallback(register_did_task, user.did, user.public_key)
                        
                        # Create DID registration record
                        DIDRegistration.objects.create(
                            did=user.did,
                            public_key=user.public_key,
                            institution=profile,
                            transaction=None  # Will be updated when task completes
                        )
                        
                        # Show appropriate message based on execution method
                        status_message = get_task_status_message(task_result)
                        if task_result['success']:
                            messages.success(request, f"Welcome to AuthentiCred! Your account has been created successfully. {status_message}")
                        else:
                            messages.warning(request, f"Account created successfully! {status_message}")
                        
                        # Schedule background trust status update (also with fallback)
                        trust_result = execute_task_with_fallback(process_did_registration_confirmation)
                        if not trust_result['success']:
                            logger.warning("Trust status update scheduling failed")
                        
                    except Exception as e:
                        logger.error(f"DID registration setup failed: {str(e)}")
                        messages.warning(request, "Account created successfully! DID registration initiated, but there was an issue with processing.")
                else:
                    # For non-institution users
                    user_type_display = dict(USER_TYPE_CHOICES).get(user.user_type, user.user_type)
                    messages.success(request, f"Welcome to AuthentiCred! Your {user_type_display.lower()} account has been created successfully.")
                
                return redirect('profile')
                
            except Exception as e:
                logger.error(f"User registration failed: {str(e)}")
                messages.error(request, "Registration failed due to an unexpected error. Please try again or contact support.")
                # Delete the user if it was created but something else failed
                if 'user' in locals():
                    user.delete()
        else:
            # Enhanced error logging and user feedback
            logger.warning(f"Registration form errors: {form.errors}")
            
            # Provide specific error messages for common issues
            if 'username' in form.errors:
                if 'unique' in str(form.errors['username']):
                    messages.error(request, "This username is already taken. Please choose a different one.")
                else:
                    messages.error(request, "Please enter a valid username.")
                    
            if 'email' in form.errors:
                if 'unique' in str(form.errors['email']):
                    messages.error(request, "This email address is already registered. Please use a different email or try logging in.")
                else:
                    messages.error(request, "Please enter a valid email address.")
                    
            if 'password2' in form.errors:
                messages.error(request, "Passwords do not match. Please ensure both password fields are identical.")
                
            if 'user_type' in form.errors:
                messages.error(request, "Please select your role in the credential ecosystem.")
                
            if 'institution_name' in form.errors:
                messages.error(request, "Institution name is required for credential issuers.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                if user.is_active:
                    login(request, user)
                    user_type_display = dict(USER_TYPE_CHOICES).get(user.user_type, user.user_type)
                    messages.success(request, f'Welcome back, {user.username}! You are logged in as a {user_type_display.lower()}.')
                    
                    # Redirect based on user type for better UX
                    if user.user_type == 'INSTITUTION':
                        return redirect('dashboard')
                    elif user.user_type == 'STUDENT':
                        return redirect('dashboard')
                    elif user.user_type == 'EMPLOYER':
                        return redirect('dashboard')
                    else:
                        return redirect('profile')
                else:
                    messages.error(request, "This account has been deactivated. Please contact support.")
            except Exception as e:
                logger.error(f"Login failed: {str(e)}")
                messages.error(request, "Login failed due to an unexpected error. Please try again.")
        else:
            # Enhanced error handling for login failures
            username = form.data.get('username', '')
            password = form.data.get('password', '')
            
            if not username and not password:
                messages.error(request, "Please enter both username/email and password.")
            elif not username:
                messages.error(request, "Please enter your username or email address.")
            elif not password:
                messages.error(request, "Please enter your password.")
            else:
                # Check if user exists but password is wrong
                try:
                    user = User.objects.get(username=username)
                    if not user.check_password(password):
                        messages.error(request, "Invalid password. Please check your password and try again.")
                    elif not user.is_active:
                        messages.error(request, "This account has been deactivated. Please contact support.")
                    else:
                        messages.error(request, "Invalid credentials. Please check your username/email and password.")
                except User.DoesNotExist:
                    try:
                        user = User.objects.get(email=username)
                        if not user.check_password(password):
                            messages.error(request, "Invalid password. Please check your password and try again.")
                        elif not user.is_active:
                            messages.error(request, "This account has been deactivated. Please contact support.")
                        else:
                            messages.error(request, "Invalid credentials. Please check your username/email and password.")
                    except User.DoesNotExist:
                        # Don't reveal if user exists for security
                        messages.error(request, "Invalid credentials. Please check your username/email and password.")
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
    
    # Redirect superusers to admin dashboard
    if user.is_superuser:
        return redirect('admin_dashboard')
    
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
        # Get WalletCredential objects instead of Credential objects
        from wallets.models import WalletCredential
        context['my_credentials'] = WalletCredential.objects.filter(
            wallet__user=user,
            is_archived=False
        ).select_related('credential')[:5]
        context['pending_actions'] = [
            {'title': 'Add New Credential', 'url': reverse('add_credential')},
            {'title': 'Share Credentials', 'url': reverse('share_all_credentials')},
        ]
    
    elif user.is_verifier():
        # Verifier dashboard with comprehensive statistics
        from credentials.models import VerificationRecord
        from django.utils import timezone
        from datetime import timedelta
        
        # Get verification statistics
        verifications = VerificationRecord.objects.filter(verifier=user)
        total_verifications = verifications.count()
        valid_verifications = verifications.filter(is_valid=True).count()
        invalid_verifications = verifications.filter(is_valid=False).count()
        
        # Calculate success rate
        success_rate = (valid_verifications / total_verifications * 100) if total_verifications > 0 else 0
        
        # Get recent verifications (last 4)
        recent_verifications = verifications.select_related('credential', 'credential__issuer', 'credential__holder')[:4]
        
        # Get verifications by source
        internal_verifications = verifications.filter(source='INTERNAL').count()
        external_verifications = verifications.filter(source='EXTERNAL').count()
        
        # Get verifications by time period
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        verifications_today = verifications.filter(verification_date__date=today).count()
        verifications_this_week = verifications.filter(verification_date__date__gte=week_ago).count()
        verifications_this_month = verifications.filter(verification_date__date__gte=month_ago).count()
        
        # Get verification details for failed verifications
        failed_verifications = verifications.filter(is_valid=False)
        common_issues = []
        if failed_verifications.exists():
            # Analyze verification details to find common issues
            for verification in failed_verifications:
                details = verification.verification_details
                if details:
                    if not details.get('signature_valid', True):
                        common_issues.append('Invalid Signature')
                    if not details.get('is_anchored', True):
                        common_issues.append('Not Blockchain Anchored')
                    if details.get('is_revoked', False):
                        common_issues.append('Credential Revoked')
                    if details.get('is_expired', False):
                        common_issues.append('Credential Expired')
                    if not details.get('issuer_trusted', True):
                        common_issues.append('Untrusted Issuer')
            
            # Count most common issues
            from collections import Counter
            issue_counts = Counter(common_issues)
            most_common_issues = issue_counts.most_common(3)
        else:
            most_common_issues = []
    
        # Get verification status breakdown
        pending_verifications = verifications.filter(is_valid__isnull=True).count()
        verified_verifications = verifications.filter(is_valid=True).count()
        rejected_verifications = verifications.filter(is_valid=False).count()
    
        context.update({
            'total_verifications': total_verifications,
            'valid_verifications': valid_verifications,
            'invalid_verifications': invalid_verifications,
            'success_rate': round(success_rate, 1),
            'recent_verifications': recent_verifications,
            'internal_verifications': internal_verifications,
            'external_verifications': external_verifications,
            'verifications_today': verifications_today,
            'verifications_this_week': verifications_this_week,
            'verifications_this_month': verifications_this_month,
            'most_common_issues': most_common_issues,
            'pending_verifications': pending_verifications,
            'verified_verifications': verified_verifications,
            'rejected_verifications': rejected_verifications,
            'pending_actions': [
                {'title': 'Verify Credentials', 'url': reverse('verify_credential')},
                {'title': 'Verification History', 'url': reverse('verification_history')},
            ],
        })
    
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

def privacy_policy_view(request):
    """Privacy Policy page"""
    return render(request, 'users/privacy_policy.html')

def terms_of_service_view(request):
    """Terms of Service page"""
    return render(request, 'users/terms_of_service.html')

def cookie_policy_view(request):
    """Cookie Policy page"""
    return render(request, 'users/cookie_policy.html')

def is_superuser(user):
    """Check if user is a superuser"""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_dashboard_view(request):
    """Admin dashboard for superusers to manage institutions and system overview"""
    
    # Get pending institutions that need approval
    pending_institutions = InstitutionProfile.objects.filter(is_trusted=False).select_related('user')
    
    # Get approved institutions
    approved_institutions = InstitutionProfile.objects.filter(is_trusted=True).select_related('user')
    
    # System statistics
    total_users = User.objects.count()
    total_institutions = InstitutionProfile.objects.count()
    total_credentials = Credential.objects.count()
    total_verifications = VerificationRecord.objects.count()
    
    # Recent activity
    recent_users = User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count()
    recent_credentials = Credential.objects.filter(issued_at__gte=timezone.now() - timedelta(days=7)).count()
    recent_verifications = VerificationRecord.objects.filter(verification_date__gte=timezone.now() - timedelta(days=7)).count()
    
    # User type distribution
    user_type_stats = User.objects.values('user_type').annotate(count=Count('user_type'))
    
    context = {
        'pending_institutions': pending_institutions,
        'approved_institutions': approved_institutions,
        'total_users': total_users,
        'total_institutions': total_institutions,
        'total_credentials': total_credentials,
        'total_verifications': total_verifications,
        'recent_users': recent_users,
        'recent_credentials': recent_credentials,
        'recent_verifications': recent_verifications,
        'user_type_stats': user_type_stats,
    }
    
    return render(request, 'users/admin_dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def approve_institution_view(request, institution_id):
    """Approve an institution"""
    if request.method == 'POST':
        institution = get_object_or_404(InstitutionProfile, id=institution_id)
        
        try:
            # Update database
            institution.is_trusted = True
            institution.save()
            
            # Update blockchain TrustRegistry
            from blockchain.services import BlockchainService
            blockchain_service = BlockchainService()
            
            # Get the institution's DID
            if institution.user.did:
                blockchain_service.update_issuer_trust_status(institution.user.did, True)
                messages.success(request, f'Institution "{institution.name}" has been approved successfully! Blockchain update initiated.')
            else:
                messages.warning(request, f'Institution "{institution.name}" approved in database, but no DID found for blockchain update.')
                
        except Exception as e:
            messages.error(request, f'Error approving institution: {str(e)}')
            
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_superuser)
def reject_institution_view(request, institution_id):
    """Reject an institution"""
    if request.method == 'POST':
        institution = get_object_or_404(InstitutionProfile, id=institution_id)
        institution_name = institution.name
        institution.delete()
        
        messages.success(request, f'Institution "{institution_name}" has been rejected and removed.')
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_superuser)
def revoke_institution_approval_view(request, institution_id):
    """Revoke approval from an institution"""
    if request.method == 'POST':
        institution = get_object_or_404(InstitutionProfile, id=institution_id)
        
        try:
            # Update database
            institution.is_trusted = False
            institution.save()
            
            # Update blockchain TrustRegistry
            from blockchain.services import BlockchainService
            blockchain_service = BlockchainService()
            
            # Get the institution's DID
            if institution.user.did:
                blockchain_service.update_issuer_trust_status(institution.user.did, False)
                messages.success(request, f'Approval revoked from institution "{institution.name}". Blockchain update initiated.')
            else:
                messages.warning(request, f'Institution "{institution.name}" revoked in database, but no DID found for blockchain update.')
                
        except Exception as e:
            messages.error(request, f'Error revoking institution: {str(e)}')
            
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')
