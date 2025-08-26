from django.core.management.base import BaseCommand
from wallets.models import Wallet
from blockchain.utils.crypto import generate_key_pair
import base64
import re

class Command(BaseCommand):
    help = 'Fix wallets with incompatible private key formats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        wallets = Wallet.objects.all()
        fixed_count = 0
        total_count = wallets.count()
        
        self.stdout.write(f"Checking {total_count} wallets for key format issues...")
        
        for wallet in wallets:
            private_key = wallet.private_key
            
            if not private_key:
                self.stdout.write(f"Wallet {wallet.id} has no private key, skipping...")
                continue
                
            # Check if it's base64 encoded (44 chars)
            if len(private_key) == 44:
                try:
                    # Try to decode as base64
                    private_key_bytes = base64.b64decode(private_key)
                    if len(private_key_bytes) == 32:  # Ed25519 key
                        self.stdout.write(f"Wallet {wallet.id} has base64 Ed25519 key, needs conversion...")
                        if not dry_run:
                            # Generate new SECP256k1 keys
                            new_private_key_hex, new_public_key_hex = generate_key_pair()
                            
                            # Update wallet
                            wallet.private_key = new_private_key_hex
                            wallet.save()
                            
                            # Update user's public key
                            wallet.user.public_key = new_public_key_hex
                            wallet.user.save()
                            
                            fixed_count += 1
                            self.stdout.write(f"✓ Fixed wallet {wallet.id}")
                        else:
                            self.stdout.write(f"Would fix wallet {wallet.id}")
                        continue
                except Exception as e:
                    self.stdout.write(f"Wallet {wallet.id} has invalid base64 key: {e}")
                    continue
            
            # Check if it's hex format but wrong length
            cleaned_key = re.sub(r'[^0-9a-fA-F]', '', private_key)
            if cleaned_key.startswith('0x'):
                cleaned_key = cleaned_key[2:]
                
            if len(cleaned_key) != 64:
                self.stdout.write(f"Wallet {wallet.id} has invalid hex key length: {len(cleaned_key)}")
                if not dry_run:
                    # Generate new keys
                    new_private_key_hex, new_public_key_hex = generate_key_pair()
                    
                    # Update wallet
                    wallet.private_key = new_private_key_hex
                    wallet.save()
                    
                    # Update user's public key
                    wallet.user.public_key = new_public_key_hex
                    wallet.user.save()
                    
                    fixed_count += 1
                    self.stdout.write(f"✓ Fixed wallet {wallet.id}")
                else:
                    self.stdout.write(f"Would fix wallet {wallet.id}")
            else:
                self.stdout.write(f"Wallet {wallet.id} has valid hex key")
        
        if dry_run:
            self.stdout.write(f"\nDry run complete. Would fix {fixed_count} wallets.")
        else:
            self.stdout.write(f"\nFixed {fixed_count} out of {total_count} wallets.")
