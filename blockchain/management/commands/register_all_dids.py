from django.core.management.base import BaseCommand
from users.models import User
from blockchain.services import BlockchainService

class Command(BaseCommand):
    help = 'Register all user DIDs on the blockchain'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force re-registration of existing DIDs')

    def handle(self, *args, **options):
        force = options['force']
        blockchain_service = BlockchainService()
        
        self.stdout.write("Registering user DIDs on blockchain...")
        self.stdout.write("=" * 50)
        
        users = User.objects.all()
        total = users.count()
        registered_count = 0
        skipped_count = 0
        error_count = 0
        
        for user in users:
            self.stdout.write(f"\nUser: {user.username} ({user.user_type})")
            self.stdout.write(f"DID: {user.did}")
            
            if not user.did:
                self.stdout.write(self.style.ERROR("✗ No DID found - skipping"))
                error_count += 1
                continue
            
            try:
                # Check if DID is already registered
                is_registered = blockchain_service.client.call_contract_function(
                    'DIDRegistry',
                    'isDIDRegistered',
                    user.did
                )
                
                if is_registered and not force:
                    self.stdout.write(self.style.SUCCESS("✓ DID already registered - skipping"))
                    skipped_count += 1
                    continue
                
                # Register DID
                public_key = user.public_key or '0x' + '0' * 64
                tx_hash = blockchain_service.register_did(user.did, public_key)
                
                self.stdout.write(self.style.SUCCESS(f"✓ DID registered with transaction: {tx_hash}"))
                registered_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to register DID: {str(e)}"))
                error_count += 1
        
        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SUMMARY:")
        self.stdout.write(f"Total users: {total}")
        self.stdout.write(f"Newly registered: {registered_count}")
        self.stdout.write(f"Skipped (already registered): {skipped_count}")
        self.stdout.write(f"Errors: {error_count}")
        
        if error_count == 0:
            self.stdout.write(self.style.SUCCESS("\n✓ All DIDs successfully processed!"))
        else:
            self.stdout.write(self.style.WARNING(f"\n⚠ {error_count} users had issues"))
