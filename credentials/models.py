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
    vc_hash = models.CharField(max_length=64, unique=True, null=True, blank=True, help_text="SHA256 hash of the credential JSON")
    
    def __str__(self):
        return f"{self.credential_type} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Compute and store the hash before saving
        if self.vc_json:
            try:
                self.vc_hash = compute_sha256(json.dumps(self.vc_json, sort_keys=True, separators=(',', ':')))
            except Exception as e:
                print(f"Error computing hash for credential {self.id}: {e}")
        super().save(*args, **kwargs)
    
    @property
    def computed_vc_hash(self):
        """Computed hash property for backward compatibility"""
        if self.vc_json is None:
            raise ValueError("Credential JSON data is None")
        if not isinstance(self.vc_json, dict):
            raise ValueError("Credential JSON data must be a dictionary")
        return compute_sha256(json.dumps(self.vc_json, sort_keys=True, separators=(',', ':')))
    
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

class VerificationRecord(models.Model):
    """Model to track verification history"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verifier = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='verifications_performed')
    credential_hash = models.CharField(max_length=64, help_text="64-character hex hash of the credential")
    credential = models.ForeignKey(Credential, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_records')
    verification_date = models.DateTimeField(default=timezone.now)
    is_valid = models.BooleanField(default=False)
    verification_details = models.JSONField(default=dict, help_text="Detailed verification results")
    source = models.CharField(max_length=20, choices=[
        ('INTERNAL', 'Internal Database'),
        ('EXTERNAL', 'External Credential'),
    ], default='INTERNAL')
    
    class Meta:
        ordering = ['-verification_date']
        indexes = [
            models.Index(fields=['verifier', '-verification_date']),
            models.Index(fields=['credential_hash']),
        ]
    
    def __str__(self):
        return f"Verification by {self.verifier.username} on {self.verification_date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def issuer_name(self):
        if self.credential and self.credential.issuer:
            return self.credential.issuer.get_full_name() or self.credential.issuer.username
        return "Unknown"
    
    @property
    def holder_name(self):
        if self.credential and self.credential.holder:
            return self.credential.holder.get_full_name() or self.credential.holder.username
        return "Unknown"
    