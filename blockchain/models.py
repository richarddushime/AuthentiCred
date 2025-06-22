# On-chain state representation
from django.db import models
from django.db.models import JSONField

class OnChainTransaction(models.Model):
    TX_TYPES = (
        ('DID_REGISTRATION', 'DID Registration'),
        ('CREDENTIAL_ANCHORING', 'Credential Anchoring'),
        ('CREDENTIAL_REVOCATION', 'Credential Revocation'),
        ('TRUST_UPDATE', 'Trust Status Update'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
    )
    
    tx_hash = models.CharField(max_length=66, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_type = models.CharField(max_length=50, choices=TX_TYPES)
    metadata = JSONField(default=dict, blank=True)
    block_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.tx_hash} ({self.get_status_display()})"

class DIDRegistration(models.Model):
    did = models.CharField(max_length=255, unique=True)
    public_key = models.TextField()
    registered_at = models.DateTimeField(auto_now_add=True)
    institution = models.ForeignKey(
        'users.InstitutionProfile', 
        on_delete=models.CASCADE,
        related_name='dids'
    )
    
    def __str__(self):
        return self.did
    