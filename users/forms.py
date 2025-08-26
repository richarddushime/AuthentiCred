from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import InstitutionProfile
from .constants import USER_TYPE_CHOICES
from django.contrib.auth import get_user_model

User = get_user_model()  

class CustomUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="I am a"
    )
    institution_name = forms.CharField(
        max_length=255, 
        required=False,
        label="Institution Name",
        help_text="Required if you're an institution"
    )
    institution_website = forms.URLField(
        required=False,
        label="Institution Website"
    )
    accreditation_proof = forms.FileField(
        required=False,
        label="Accreditation Proof",
        help_text="Upload documentation proving your accreditation status"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        if user_type == 'INSTITUTION':
            if not cleaned_data.get('institution_name'):
                self.add_error('institution_name', 'This field is required for institutions')
                
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data['user_type']
        
        if commit:
            user.save()
            
            if user_type == 'INSTITUTION':
                InstitutionProfile.objects.create(
                    user=user,
                    name=self.cleaned_data['institution_name'],
                    website=self.cleaned_data['institution_website'],
                    accreditation_proof=self.cleaned_data['accreditation_proof']
                )
                
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )

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
