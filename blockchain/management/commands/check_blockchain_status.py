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

class Command(BaseCommand):
    help = 'Check blockchain status and contract connectivity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed contract information',
        )
        parser.add_argument(
            '--ganache-port',
            type=int,
            default=8545,
            help='Ganache port (default: 8545)',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        ganache_port = options['ganache_port']
        
        self.stdout.write("🔍 AuthentiCred Blockchain Status Check")
        self.stdout.write("=" * 50)
        
        # Check Ganache connection
        self.check_ganache_connection(ganache_port)
        
        # Check contract addresses
        self.check_contract_addresses()
        
        # Check contract connectivity
        if detailed:
            self.check_contract_connectivity(ganache_port)
        
        # Check ABI files
        self.check_abi_files()
        
        self.stdout.write(self.style.SUCCESS("\n✅ Blockchain status check completed!"))

    def check_ganache_connection(self, ganache_port):
        """Check Ganache connection"""
        self.stdout.write(f"\n🔗 Checking Ganache connection (port: {ganache_port})...")
        
        try:
            w3 = Web3(Web3.HTTPProvider(f'http://127.0.0.1:{ganache_port}'))
            
            if w3.is_connected():
                self.stdout.write("✅ Ganache is connected")
                
                # Get network info
                chain_id = w3.eth.chain_id
                block_number = w3.eth.block_number
                accounts = w3.eth.accounts
                
                self.stdout.write(f"  📊 Chain ID: {chain_id}")
                self.stdout.write(f"  📦 Block Number: {block_number}")
                self.stdout.write(f"  👥 Accounts: {len(accounts)}")
                
                if accounts:
                    self.stdout.write(f"  💰 First Account: {accounts[0]}")
                    balance = w3.eth.get_balance(accounts[0])
                    balance_eth = w3.from_wei(balance, 'ether')
                    self.stdout.write(f"  💎 Balance: {balance_eth} ETH")
            else:
                self.stdout.write(self.style.ERROR("❌ Ganache is not connected"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to connect to Ganache: {e}"))

    def check_contract_addresses(self):
        """Check contract addresses in settings"""
        self.stdout.write("\n📋 Checking contract addresses...")
        
        contracts = [
            ('DID Registry', settings.DIDREGISTRY_ADDRESS),
            ('Trust Registry', settings.TRUSTREGISTRY_ADDRESS),
            ('Credential Anchor', settings.CREDENTIALANCHOR_ADDRESS),
            ('Revocation Registry', settings.REVOCATIONREGISTRY_ADDRESS),
        ]
        
        for name, address in contracts:
            if address:
                self.stdout.write(f"  ✅ {name}: {address}")
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  {name}: Not set"))

    def check_contract_connectivity(self, ganache_port):
        """Check contract connectivity"""
        self.stdout.write("\n🔗 Checking contract connectivity...")
        
        try:
            w3 = Web3(Web3.HTTPProvider(f'http://127.0.0.1:{ganache_port}'))
            
            if not w3.is_connected():
                self.stdout.write(self.style.ERROR("❌ Cannot check contracts - Ganache not connected"))
                return
            
            contracts = [
                ('DID Registry', settings.DIDREGISTRY_ADDRESS),
                ('Trust Registry', settings.TRUSTREGISTRY_ADDRESS),
                ('Credential Anchor', settings.CREDENTIALANCHOR_ADDRESS),
                ('Revocation Registry', settings.REVOCATIONREGISTRY_ADDRESS),
            ]
            
            for name, address in contracts:
                if not address:
                    self.stdout.write(f"  ⚠️  {name}: Address not set")
                    continue
                
                try:
                    # Check if contract exists at address
                    code = w3.eth.get_code(address)
                    if code and code != b'':
                        self.stdout.write(f"  ✅ {name}: Contract deployed and accessible")
                    else:
                        self.stdout.write(self.style.ERROR(f"  ❌ {name}: No contract at address"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ {name}: Error checking contract - {e}"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to check contracts: {e}"))

    def check_abi_files(self):
        """Check ABI files"""
        self.stdout.write("\n📄 Checking ABI files...")
        
        base_dir = Path(settings.BASE_DIR)
        abis_path = base_dir / 'blockchain' / 'abis'
        
        if not abis_path.exists():
            self.stdout.write(self.style.ERROR(f"❌ ABIs directory not found: {abis_path}"))
            return
        
        contract_files = [
            'DIDRegistry.json',
            'TrustRegistry.json',
            'CredentialAnchor.json',
            'RevocationRegistry.json'
        ]
        
        for contract_file in contract_files:
            abi_path = abis_path / contract_file
            if abi_path.exists():
                try:
                    with open(abi_path, 'r') as f:
                        data = json.load(f)
                    
                    if 'abi' in data and 'bytecode' in data:
                        self.stdout.write(f"  ✅ {contract_file}: Valid ABI and bytecode")
                    else:
                        self.stdout.write(self.style.WARNING(f"  ⚠️  {contract_file}: Missing ABI or bytecode"))
                except json.JSONDecodeError:
                    self.stdout.write(self.style.ERROR(f"  ❌ {contract_file}: Invalid JSON"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ {contract_file}: Error reading file - {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  {contract_file}: Not found"))
