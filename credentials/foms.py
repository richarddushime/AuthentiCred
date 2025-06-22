# credentials/forms.py
from django import forms
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
    
    class Meta:
        model = Credential
        fields = ['title', 'description', 'expiration_date']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
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
    