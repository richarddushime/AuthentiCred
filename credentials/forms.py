# credentials/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Credential, CredentialSchema
from users.models import User
from django.forms import formset_factory

class CredentialSchemaForm(forms.ModelForm):
    class Meta:
        model = CredentialSchema
        fields = ['name', 'type', 'fields']
        widgets = {
            'fields': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '{"field_name": "type", "gpa": "float", "degree": "str"}'
            }),
        }

class CredentialIssueForm(forms.ModelForm):
    holder_email = forms.EmailField(label="Recipient Email")
    document = forms.FileField(
        label="Upload Document/Certificate",
        required=False,
        help_text="Upload PDF, JPG, PNG, or other document formats (max 10MB)",
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp,.doc,.docx,.txt',
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
        })
    )
    
    class Meta:
        model = Credential
        fields = ['title', 'description', 'expiration_date', 'document']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_document(self):
        document = self.cleaned_data.get('document')
        if document:
            # Check file size (10MB limit)
            if document.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise forms.ValidationError("File size must be under 10MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.doc', '.docx', '.txt']
            file_extension = '.' + document.name.split('.')[-1].lower() if '.' in document.name else ''
            
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        return document
    
    def __init__(self, *args, issuer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.issuer = issuer
        
        # Add dynamic fields based on schema
        if 'schema' in self.initial:
            schema = self.initial['schema']
            if schema and schema.fields:
                for field_name, field_type in schema.fields.items():
                    if field_type == 'str':
                        self.fields[field_name] = forms.CharField(
                            label=field_name.capitalize(),
                            required=False
                        )
                    elif field_type == 'int':
                        self.fields[field_name] = forms.IntegerField(
                            label=field_name.capitalize(),
                            required=False
                        )
                    elif field_type == 'float':
                        self.fields[field_name] = forms.FloatField(
                            label=field_name.capitalize(),
                            required=False,
                            validators=[MinValueValidator(0.0), MaxValueValidator(4.0)]
                        )
                    elif field_type == 'date':
                        self.fields[field_name] = forms.DateField(
                            label=field_name.capitalize(),
                            required=False,
                            widget=forms.DateInput(attrs={'type': 'date'})
                        )
                    elif field_type == 'bool':
                        self.fields[field_name] = forms.BooleanField(
                            label=field_name.capitalize(),
                            required=False
                        )

class CredentialRevokeForm(forms.Form):
    reason = forms.CharField(
        label="Revocation Reason",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True
    )
    