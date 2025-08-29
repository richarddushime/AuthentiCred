from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import InstitutionProfile
from blockchain.services import BlockchainService

User = get_user_model()

class Command(BaseCommand):
    help = 'Approve an issuer on the blockchain TrustRegistry'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the institution to approve')
        parser.add_argument('--trusted', action='store_true', default=True, help='Set trust status (default: True)')

    def handle(self, *args, **options):
        username = options['username']
        trusted = options['trusted']
        
        try:
            # Find the user
            user = User.objects.get(username=username)
            
            if not user.is_issuer():
                self.stdout.write(
                    self.style.ERROR(f'User {username} is not an institution')
                )
                return
            
            # Check if user has a DID
            if not user.did:
                self.stdout.write(
                    self.style.ERROR(f'User {username} does not have a DID registered')
                )
                return
            
            # Update institution profile
            try:
                profile = InstitutionProfile.objects.get(user=user)
                profile.is_trusted = trusted
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated institution profile for {username}')
                )
            except InstitutionProfile.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'No institution profile found for {username}, creating one')
                )
                InstitutionProfile.objects.create(user=user, is_trusted=trusted)
            
            # Update blockchain
            blockchain_service = BlockchainService()
            blockchain_service.update_issuer_trust_status(user.did, trusted)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully {"approved" if trusted else "revoked"} issuer {username} (DID: {user.did}) on blockchain'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error approving issuer: {str(e)}')
            )
