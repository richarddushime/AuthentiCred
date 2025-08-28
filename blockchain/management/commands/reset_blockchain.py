#!/usr/bin/env python3
"""
Django management command for resetting blockchain state
======================================================

This command resets the blockchain state and clears contract data.

Usage:
    python manage.py reset_blockchain [options]

Options:
    --confirm     Confirm the reset operation
    --ganache-port Ganache port (default: 8545)
    --clear-db     Also clear database records
"""

import json
from pathlib import Path
from web3 import Web3
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

class Command(BaseCommand):
    help = 'Reset blockchain state and clear contract data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the reset operation',
        )
        parser.add_argument(
            '--ganache-port',
            type=int,
            default=7545,
            help='Ganache port (default: 7545)',
        )
        parser.add_argument(
            '--clear-db',
            action='store_true',
            help='Also clear database records',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        ganache_port = options['ganache_port']
        clear_db = options['clear_db']
        
        self.stdout.write("⚠️  AuthentiCred Blockchain Reset")
        self.stdout.write("=" * 50)
        
        if not confirm:
            self.stdout.write(self.style.WARNING(
                "⚠️  This will reset the blockchain state and clear contract data!\n"
                "Use --confirm to proceed."
            ))
            return
        
        # Check Ganache connection
        if not self.check_ganache_connection(ganache_port):
            raise CommandError("Cannot reset - Ganache not connected")
        
        # Clear contract addresses from settings
        self.clear_contract_addresses()
        
        # Clear ABI files
        self.clear_abi_files()
        
        # Clear database records if requested
        if clear_db:
            self.clear_database_records()
        
        self.stdout.write(self.style.SUCCESS("\n✅ Blockchain reset completed!"))

    def check_ganache_connection(self, ganache_port):
        """Check Ganache connection"""
        self.stdout.write(f"🔗 Checking Ganache connection (port: {ganache_port})...")
        
        try:
            w3 = Web3(Web3.HTTPProvider(f'http://127.0.0.1:{ganache_port}'))
            
            if w3.is_connected():
                self.stdout.write("✅ Ganache is connected")
                return True
            else:
                self.stdout.write(self.style.ERROR("❌ Ganache is not connected"))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to connect to Ganache: {e}"))
            return False

    def clear_contract_addresses(self):
        """Clear contract addresses from .env file"""
        self.stdout.write("\n🗑️  Clearing contract addresses...")
        
        env_file = Path(settings.BASE_DIR) / '.env'
        
        if not env_file.exists():
            self.stdout.write("⚠️  .env file not found")
            return
        
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Clear contract addresses
            contract_vars = [
                'DIDREGISTRY_ADDRESS',
                'TRUSTREGISTRY_ADDRESS',
                'CREDENTIALANCHOR_ADDRESS',
                'REVOCATIONREGISTRY_ADDRESS',
                'BLOCKCHAIN_OPERATOR_KEY',
                'BLOCKCHAIN_OPERATOR_ADDRESS',
            ]
            
            updated_lines = []
            for line in lines:
                should_keep = True
                for var in contract_vars:
                    if line.startswith(f'{var}='):
                        updated_lines.append(f'{var}=\n')
                        should_keep = False
                        break
                
                if should_keep:
                    updated_lines.append(line)
            
            with open(env_file, 'w') as f:
                f.writelines(updated_lines)
            
            self.stdout.write("✅ Contract addresses cleared from .env")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to clear contract addresses: {e}"))

    def clear_abi_files(self):
        """Clear ABI files"""
        self.stdout.write("\n🗑️  Clearing ABI files...")
        
        base_dir = Path(settings.BASE_DIR)
        abis_path = base_dir / 'blockchain' / 'abis'
        
        if not abis_path.exists():
            self.stdout.write("⚠️  ABIs directory not found")
            return
        
        contract_files = [
            'DIDRegistry.json',
            'TrustRegistry.json',
            'CredentialAnchor.json',
            'RevocationRegistry.json'
        ]
        
        cleared_count = 0
        for contract_file in contract_files:
            abi_path = abis_path / contract_file
            if abi_path.exists():
                try:
                    abi_path.unlink()
                    self.stdout.write(f"  🗑️  Removed: {contract_file}")
                    cleared_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ Failed to remove {contract_file}: {e}"))
        
        self.stdout.write(f"✅ Cleared {cleared_count} ABI files")

    def clear_database_records(self):
        """Clear database records"""
        self.stdout.write("\n🗑️  Clearing database records...")
        
        try:
            with transaction.atomic():
                # Import models here to avoid circular imports
                from blockchain.models import DIDRegistration, OnChainTransaction
                from credentials.models import Credential, VerificationRecord
                
                # Clear blockchain records
                did_count = DIDRegistration.objects.count()
                DIDRegistration.objects.all().delete()
                
                tx_count = OnChainTransaction.objects.count()
                OnChainTransaction.objects.all().delete()
                
                # Clear credential records
                cred_count = Credential.objects.count()
                Credential.objects.all().delete()
                
                verif_count = VerificationRecord.objects.count()
                VerificationRecord.objects.all().delete()
                
                self.stdout.write(f"  🗑️  Cleared {did_count} DID registrations")
                self.stdout.write(f"  🗑️  Cleared {tx_count} transactions")
                self.stdout.write(f"  🗑️  Cleared {cred_count} credentials")
                self.stdout.write(f"  🗑️  Cleared {verif_count} verifications")
            
            self.stdout.write("✅ Database records cleared")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to clear database records: {e}"))
