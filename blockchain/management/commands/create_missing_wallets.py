#!/usr/bin/env python3
"""
Django management command for creating missing wallets
====================================================

This command creates wallets for users who don't have them.

Usage:
    python manage.py create_missing_wallets [options]

Options:
    --force     Force recreation of existing wallets
    --dry-run   Show what would be done without making changes
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from blockchain.utils.crypto import generate_key_pair
from wallets.models import Wallet

class Command(BaseCommand):
    help = 'Creates wallets for users without them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing wallets',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        
        User = get_user_model()
        
        if force:
            users_to_process = User.objects.all()
            self.stdout.write("🔄 Processing all users (force mode)...")
        else:
            users_to_process = User.objects.filter(wallet__isnull=True)
            self.stdout.write("🔄 Processing users without wallets...")
        
        if dry_run:
            self.stdout.write(f"📋 Would process {users_to_process.count()} users")
            for user in users_to_process:
                if hasattr(user, 'wallet'):
                    self.stdout.write(f"  ⚠️  {user.email} (has wallet)")
                else:
                    self.stdout.write(f"  ➕ {user.email} (no wallet)")
            return
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for user in users_to_process:
                try:
                    if hasattr(user, 'wallet') and not force:
                        self.stdout.write(f"⏭️  Skipping {user.email} (already has wallet)")
                        continue
                    
                    # Generate new key pair
                    private_key, public_key = generate_key_pair()
                    
                    if hasattr(user, 'wallet') and force:
                        # Update existing wallet
                        user.wallet.private_key = private_key
                        user.wallet.save()
                        user.public_key = public_key
                        user.save()
                        self.stdout.write(f"🔄 Updated wallet for {user.email}")
                        updated_count += 1
                    else:
                        # Create new wallet
                        Wallet.objects.create(user=user, private_key=private_key)
                        user.public_key = public_key
                        user.save()
                        self.stdout.write(f"✅ Created wallet for {user.email}")
                        created_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Failed to create wallet for {user.email}: {e}")
                    )
        
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Wallet creation completed!\n"
            f"  ➕ Created: {created_count}\n"
            f"  🔄 Updated: {updated_count}\n"
            f"  📊 Total processed: {created_count + updated_count}"
        ))
        