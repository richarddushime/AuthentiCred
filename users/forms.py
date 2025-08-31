from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import InstitutionProfile
from .constants import USER_TYPE_CHOICES
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()  

class CustomUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),  # Hide the default radio buttons but keep them functional
        label="I am a:",
        help_text="Select your role in the credential ecosystem"
    )
    institution_name = forms.CharField(
        max_length=255, 
        required=False,
        label="Institution Name",
        help_text="Required if you're an institution",
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter your institution name'
        })
    )
    institution_website = forms.URLField(
        required=False,
        label="Institution Website",
        help_text="Optional: Your institution's website URL",
        widget=forms.URLInput(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'https://your-institution.com'
        })
    )
    accreditation_proof = forms.FileField(
        required=False,
        label="Accreditation Proof",
        help_text="Upload documentation proving your accreditation status",
        widget=forms.FileInput(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        
        # Add custom styling to form fields
        for field_name, field in self.fields.items():
            if field_name not in ['user_type', 'institution_name', 'institution_website', 'accreditation_proof']:
                field.widget.attrs.update({
                    'class': 'block w-full px-3 py-2 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        if user_type == 'INSTITUTION':
            institution_name = cleaned_data.get('institution_name')
            if not institution_name or institution_name.strip() == '':
                self.add_error('institution_name', 'Institution name is required for credential issuers')
            
            # Validate institution name length
            if institution_name and len(institution_name.strip()) < 3:
                self.add_error('institution_name', 'Institution name must be at least 3 characters long')
            
            # Validate website if provided
            website = cleaned_data.get('institution_website')
            if website and not website.startswith(('http://', 'https://')):
                cleaned_data['institution_website'] = 'https://' + website
                
        elif user_type == 'STUDENT':
            # Additional validation for students if needed
            pass
            
        elif user_type == 'EMPLOYER':
            # Additional validation for employers if needed
            pass
            
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data['user_type']
        
        if commit:
            user.save()
            
            if user_type == 'INSTITUTION':
                InstitutionProfile.objects.create(
                    user=user,
                    name=self.cleaned_data['institution_name'].strip(),
                    website=self.cleaned_data['institution_website'],
                    accreditation_proof=self.cleaned_data['accreditation_proof']
                )
                
        return user

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if len(username) < 3:
                raise ValidationError('Username must be at least 3 characters long.')
            if not username.replace('_', '').replace('-', '').isalnum():
                raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email is already registered
            if User.objects.filter(email=email).exists():
                raise ValidationError('This email address is already registered. Please use a different email or try logging in.')
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
            if password1.isdigit():
                raise ValidationError('Password cannot be entirely numeric.')
            if password1.lower() == password1:
                raise ValidationError('Password must contain at least one uppercase letter.')
        return password1

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter your password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    raise ValidationError('This account has been deactivated. Please contact support.')
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=username)
                    if not user.is_active:
                        raise ValidationError('This account has been deactivated. Please contact support.')
                except User.DoesNotExist:
                    # Don't reveal if username/email exists or not for security
                    pass
                    
        return cleaned_data

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].help_text = 'Enter a valid email address'

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Your password must contain at least 8 characters.'
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Current password is incorrect.')
        return current_password
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2
    
    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

class DeleteAccountForm(forms.Form):
    confirm_delete = forms.BooleanField(
        label='I understand that this action cannot be undone',
        required=True
    )
    password = forms.CharField(
        label='Enter your password to confirm',
        widget=forms.PasswordInput
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Password is incorrect.')
        return password

class InstitutionSettingsForm(forms.ModelForm):
    class Meta:
        model = InstitutionProfile
        fields = ['name', 'website', 'description', 'accreditation_proof']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label='Your Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name'})
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'})
    )
    subject = forms.CharField(
        max_length=200,
        label='Subject',
        widget=forms.TextInput(attrs={'placeholder': 'What is this about?'})
    )
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Tell us more about your inquiry...'
        })
    )
