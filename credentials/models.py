# credentials/models.py
import uuid
import json
from django.db import models
from django.utils import timezone
from blockchain.utils.vc_proofs import compute_sha256
from django.core.validators import MinValueValidator, MaxValueValidator

class CredentialSchema(models.Model):
    SCHEMA_TYPES = (
        ('DEGREE', 'Academic Degree'),
        ('CERTIFICATE', 'Professional Certificate'),
        ('BADGE', 'Digital Badge'),
        ('TRANSCRIPT', 'Academic Transcript'),
        ('OTHER', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default="1.0")
    type = models.CharField(max_length=50, choices=SCHEMA_TYPES, default='OTHER')
    fields = models.JSONField(help_text="JSON structure defining the credential fields")
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='schemas')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (v{self.version})"

class Credential(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('REVOKED', 'Revoked'),
        ('EXPIRED', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vc_json = models.JSONField()
    issuer = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='issued_credentials')
    holder = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='credentials')
    schema = models.ForeignKey(CredentialSchema, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    credential_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(default=timezone.now)
    issued_at = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.credential_type} - {self.title}"
    
    @property
    def vc_hash(self):
        return compute_sha256(json.dumps(self.vc_json))
    
    def issue(self):
        if self.status == 'DRAFT':
            self.status = 'ISSUED'
            self.issued_at = timezone.now()
            self.save()
            return True
        return False
    
    def revoke(self, reason=""):
        if self.status == 'ISSUED':
            self.status = 'REVOKED'
            self.revocation_reason = reason
            self.save()
            return True
        return False
    