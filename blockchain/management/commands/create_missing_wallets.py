# management/commands/create_missing_wallets.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wallets.utils import generate_key_pair
from wallets.models import Wallet

class Command(BaseCommand):
    help = 'Creates wallets for users without them'

    def handle(self, *args, **options):
        User = get_user_model()
        users_without_wallets = User.objects.filter(wallet__isnull=True)
        
        for user in users_without_wallets:
            private_key, public_key = generate_key_pair()
            Wallet.objects.create(user=user, private_key=private_key)
            user.public_key = public_key
            user.save()
            self.stdout.write(f'Created wallet for {user.email}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {users_without_wallets.count()} wallets'))
        