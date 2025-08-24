# wallets/models.py
import uuid
from django.db import models
# from encrypted_model_fields.fields import EncryptedCharField  # Temporarily commented out
from credentials.models import Credential

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='wallet')
    name = models.CharField(max_length=100, default="My AuthentiCred Wallet")
    private_key = models.CharField(max_length=255)  # Temporarily use regular CharField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Wallet"

class WalletCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='wallet_credentials')
    credential = models.ForeignKey('credentials.Credential', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('wallet', 'credential')
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.credential.credential_type} in {self.wallet}"
    