import re
from django.db import migrations

def fix_short_keys(apps, schema_editor):
    Wallet = apps.get_model('wallets', 'Wallet')  
    for wallet in Wallet.objects.all():
        key = wallet.private_key
        if key:  # Handle empty keys
            # Clean and validate key
            cleaned_key = re.sub(r'[^0-9a-fA-F]', '', key)
            if cleaned_key.startswith('0x'):
                cleaned_key = cleaned_key[2:]
            if len(cleaned_key) < 64:  # Check if still too short
                print(f"Deleting invalid wallet {wallet.id} (key: {key})")
                wallet.delete()

class Migration(migrations.Migration):
    dependencies = [
        ('wallets', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(fix_short_keys),
    ]
    