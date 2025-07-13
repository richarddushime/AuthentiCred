from django.db import models
from django.utils import timezone
from .constants import USER_TYPE_CHOICES
from blockchain.utils.vc_proofs import generate_key_pair
import uuid
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    did = models.CharField(max_length=255, unique=True, null=True, blank=True)
    public_key = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="user",
    )
    
    def save(self, *args, **kwargs):
        if not self.did and self.user_type == 'INSTITUTION':
            # private_key, public_key = generate_key_pair()
            # self.public_key = public_key.hex()
            self.did = f"did:authenticred:{self.id}"
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('profile')
    
    def is_issuer(self):
        return self.user_type == 'INSTITUTION'

    def get_trust_status(self):
        if self.user_type == 'INSTITUTION':
            try:
                profile = self.institution_profile
                return profile.is_trusted
            except InstitutionProfile.DoesNotExist:
                pass
        return False
    
    def is_holder(self):
        return self.user_type == 'STUDENT'
    
    def is_verifier(self):
        return self.user_type == 'EMPLOYER'
    @property
    def did(self):
        if self.public_key:
            return f"did:authenticred:{self.public_key}"
        return None
    
class InstitutionProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution_profile')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    accreditation_proof = models.FileField(upload_to='accreditations/', null=True, blank=True)
    is_trusted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    