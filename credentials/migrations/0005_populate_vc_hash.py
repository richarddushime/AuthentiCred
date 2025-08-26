# Generated manually
from django.db import migrations
from blockchain.utils.vc_proofs import compute_sha256
import json

def populate_vc_hash(apps, schema_editor):
    Credential = apps.get_model('credentials', 'Credential')
    
    for credential in Credential.objects.all():
        if credential.vc_json:
            try:
                # Compute the hash
                vc_hash = compute_sha256(json.dumps(credential.vc_json, sort_keys=True, separators=(',', ':')))
                credential.vc_hash = vc_hash
                credential.save(update_fields=['vc_hash'])
                print(f"Populated hash for credential {credential.id}: {vc_hash}")
            except Exception as e:
                print(f"Error computing hash for credential {credential.id}: {e}")

def reverse_populate_vc_hash(apps, schema_editor):
    Credential = apps.get_model('credentials', 'Credential')
    Credential.objects.update(vc_hash=None)

class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0004_credential_vc_hash'),
    ]

    operations = [
        migrations.RunPython(populate_vc_hash, reverse_populate_vc_hash),
    ]
