#!/usr/bin/env python3
"""
Django management command for checking blockchain status
======================================================

This command checks the status of blockchain connections and contracts.

Usage:
    python manage.py check_blockchain_status [options]

Options:
    --detailed    Show detailed contract information
    --ganache-port Ganache port (default: 8545)
"""

import json
from pathlib import Path
from web3 import Web3
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from credentials.models import Credential
from blockchain.services import BlockchainService

class Command(BaseCommand):
    help = 'Check blockchain status for all credentials'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Attempt to fix missing blockchain entries')

    def handle(self, *args, **options):
        fix = options['fix']
        blockchain_service = BlockchainService()
        
        self.stdout.write("Checking blockchain status for all credentials...")
        self.stdout.write("=" * 60)
        
        credentials = Credential.objects.all()
        total = credentials.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING("No credentials found in database"))
            return
        
        anchored_count = 0
        trusted_issuers = 0
        revoked_count = 0
        
        for cred in credentials:
            self.stdout.write(f"\nCredential: {cred.title} (ID: {cred.id})")
            self.stdout.write(f"Issuer: {cred.issuer.username} (DID: {cred.issuer.did})")
            
            # Check anchoring
            try:
                is_anchored = blockchain_service.client.call_contract_function(
                    'CredentialAnchor',
                    'verifyProof',
                    cred.vc_hash
                )
                if is_anchored:
                    self.stdout.write(self.style.SUCCESS(f"✓ Anchored on blockchain"))
                    anchored_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"✗ Not anchored on blockchain"))
                    if fix:
                        try:
                            tx_hash = blockchain_service.anchor_credential(cred.vc_hash)
                            self.stdout.write(self.style.SUCCESS(f"  → Anchored with transaction: {tx_hash}"))
                            anchored_count += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  → Failed to anchor: {str(e)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error checking anchoring: {str(e)}"))
            
            # Check issuer trust
            try:
                is_trusted = blockchain_service.is_issuer_registered(cred.issuer.did)
                if is_trusted:
                    self.stdout.write(self.style.SUCCESS(f"✓ Issuer trusted on blockchain"))
                    trusted_issuers += 1
                else:
                    self.stdout.write(self.style.WARNING(f"✗ Issuer not trusted on blockchain"))
                    if fix:
                        try:
                            blockchain_service.update_issuer_trust_status(cred.issuer.did, True)
                            self.stdout.write(self.style.SUCCESS(f"  → Issuer trust status updated"))
                            trusted_issuers += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  → Failed to update trust status: {str(e)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error checking issuer trust: {str(e)}"))
            
            # Check revocation
            try:
                is_revoked = blockchain_service.is_credential_revoked(str(cred.id))
                if is_revoked:
                    self.stdout.write(self.style.ERROR(f"✗ Credential revoked on blockchain"))
                    revoked_count += 1
                else:
                    self.stdout.write(self.style.SUCCESS(f"✓ Credential not revoked"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error checking revocation: {str(e)}"))
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY:")
        self.stdout.write(f"Total credentials: {total}")
        self.stdout.write(f"Anchored on blockchain: {anchored_count}/{total}")
        self.stdout.write(f"Trusted issuers: {trusted_issuers}/{total}")
        self.stdout.write(f"Revoked credentials: {revoked_count}/{total}")
        
        if anchored_count == total and trusted_issuers == total and revoked_count == 0:
            self.stdout.write(self.style.SUCCESS("\n✓ All credentials are properly configured on blockchain!"))
        else:
            self.stdout.write(self.style.WARNING(f"\n⚠ {total - anchored_count} credentials need anchoring"))
            self.stdout.write(self.style.WARNING(f"⚠ {total - trusted_issuers} issuers need trust status update"))
            if revoked_count > 0:
                self.stdout.write(self.style.ERROR(f"⚠ {revoked_count} credentials are revoked"))
