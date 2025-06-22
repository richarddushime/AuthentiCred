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
