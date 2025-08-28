#!/usr/bin/env python3
"""
Django management command for complete contract deployment workflow
==================================================================

This command:
1. Copies JSON files from Truffle build to abis folder
2. Deploys contracts using Truffle
3. Updates .env file with contract addresses
4. Updates settings with new addresses

Usage:
    python manage.py deploy_contracts_complete
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from web3 import Web3
from eth_account import Account

class Command(BaseCommand):
    help = 'Complete contract deployment workflow with JSON copying and address updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-truffle-deploy',
            action='store_true',
            help='Skip Truffle deployment (only copy JSONs and update addresses)',
        )
        parser.add_argument(
            '--skip-json-copy',
            action='store_true',
            help='Skip copying JSON files (only deploy and update addresses)',
        )
        parser.add_argument(
            '--skip-env-update',
            action='store_true',
            help='Skip updating .env file (only deploy and copy JSONs)',
        )
        parser.add_argument(
            '--ganache-port',
            type=int,
            default=8545,
            help='Ganache port (default: 8545)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting complete contract deployment workflow...'))
        
        # Get paths
        base_dir = Path(settings.BASE_DIR)
        truffle_dir = base_dir / 'blockchain' / 'Authenticred_contracts'
        abis_dir = base_dir / 'blockchain' / 'abis'
        env_file = base_dir / '.env'
        
        # Step 1: Copy JSON files from Truffle build to abis folder
        if not options['skip_json_copy']:
            self.copy_json_files(truffle_dir, abis_dir)
        
        # Step 2: Deploy contracts using Truffle
        if not options['skip_truffle_deploy']:
            self.deploy_contracts(truffle_dir, options['ganache_port'])
        
        # Step 3: Update .env file with contract addresses
        if not options['skip_env_update']:
            self.update_env_file(env_file, truffle_dir)
        
        self.stdout.write(self.style.SUCCESS('✅ Complete contract deployment workflow finished!'))

    def copy_json_files(self, truffle_dir, abis_dir):
        """Copy JSON files from Truffle build to abis folder"""
        self.stdout.write('📋 Copying JSON files from Truffle build...')
        
        build_dir = truffle_dir / 'build' / 'contracts'
        if not build_dir.exists():
            raise CommandError(f'Truffle build directory not found: {build_dir}')
        
        # Ensure abis directory exists
        abis_dir.mkdir(parents=True, exist_ok=True)
        
        # Contract names to copy
        contracts = [
            'DIDRegistry',
            'TrustRegistry', 
            'CredentialAnchor',
            'RevocationRegistry'
        ]
        
        copied_count = 0
        for contract in contracts:
            source_file = build_dir / f'{contract}.json'
            dest_file = abis_dir / f'{contract}.json'
            
            if source_file.exists():
                shutil.copy2(source_file, dest_file)
                self.stdout.write(f'  ✅ Copied {contract}.json')
                copied_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  {contract}.json not found in build'))
        
        self.stdout.write(f'📋 Copied {copied_count} JSON files')

    def deploy_contracts(self, truffle_dir, ganache_port):
        """Deploy contracts using Truffle"""
        self.stdout.write('🔗 Deploying contracts with Truffle...')
        
        # Check if Ganache is running
        if not self.is_ganache_running(ganache_port):
            raise CommandError(f'Ganache is not running on port {ganache_port}. Please start Ganache first.')
        
        # Update truffle-config.js with correct port
        self.update_truffle_config(truffle_dir, ganache_port)
        
        # Run Truffle deployment
        try:
            cmd = ['truffle', 'migrate', '--reset', '--network', 'development']
            result = subprocess.run(
                cmd,
                cwd=truffle_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.stdout.write('✅ Contracts deployed successfully')
            self.stdout.write(result.stdout)
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Contract deployment failed: {e.stderr}'))
            raise CommandError('Contract deployment failed')

    def update_truffle_config(self, truffle_dir, ganache_port):
        """Update truffle-config.js with correct Ganache port"""
        config_file = truffle_dir / 'truffle-config.js'
        
        if not config_file.exists():
            self.stdout.write(self.style.WARNING('⚠️  truffle-config.js not found, skipping update'))
            return
        
        # Read current config
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Update port in development network
        import re
        updated_content = re.sub(
            r'port:\s*\d+',
            f'port: {ganache_port}',
            content
        )
        
        # Write updated config
        with open(config_file, 'w') as f:
            f.write(updated_content)
        
        self.stdout.write(f'  ✅ Updated truffle-config.js with port {ganache_port}')

    def update_env_file(self, env_file, truffle_dir):
        """Update .env file with contract addresses"""
        self.stdout.write('⚙️  Updating .env file with contract addresses...')
        
        # Read contract addresses from Truffle build
        addresses = self.get_contract_addresses(truffle_dir)
        
        # Generate operator account
        operator_account = self.generate_operator_account()
        
        # Read existing .env file or create from example
        env_content = self.read_env_file(env_file)
        
        # Update or add contract addresses
        updates = {
            'DIDREGISTRY_ADDRESS': addresses.get('DIDRegistry', ''),
            'TRUSTREGISTRY_ADDRESS': addresses.get('TrustRegistry', ''),
            'CREDENTIALANCHOR_ADDRESS': addresses.get('CredentialAnchor', ''),
            'REVOCATIONREGISTRY_ADDRESS': addresses.get('RevocationRegistry', ''),
            'BLOCKCHAIN_OPERATOR_KEY': operator_account['private_key'],
            'BLOCKCHAIN_OPERATOR_ADDRESS': operator_account['address'],
            'BLOCKCHAIN_RPC_URL': 'http://127.0.0.1:8545',
            'GANACHE_CHAIN_ID': '5777',
            'BLOCKCHAIN_NETWORK': 'ganache',
        }
        
        # Apply updates
        for key, value in updates.items():
            env_content = self.update_env_variable(env_content, key, value)
        
        # Write updated .env file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        self.stdout.write('✅ .env file updated successfully')
        
        # Display addresses
        self.stdout.write('\n📋 Contract Addresses:')
        for name, addr in addresses.items():
            self.stdout.write(f'  {name}: {addr}')
        
        self.stdout.write(f'\n🔑 Operator Account: {operator_account["address"]}')

    def get_contract_addresses(self, truffle_dir):
        """Extract contract addresses from Truffle build"""
        addresses = {}
        
        # Read addresses from build artifacts
        build_dir = truffle_dir / 'build' / 'contracts'
        contracts = ['DIDRegistry', 'TrustRegistry', 'CredentialAnchor', 'RevocationRegistry']
        
        for contract in contracts:
            json_file = build_dir / f'{contract}.json'
            if json_file.exists():
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if 'networks' in data and '5777' in data['networks']:
                        addresses[contract] = data['networks']['5777']['address']
        
        return addresses

    def generate_operator_account(self):
        """Generate a new operator account"""
        account = Account.create()
        return {
            'address': account.address,
            'private_key': account.key.hex()
        }

    def read_env_file(self, env_file):
        """Read .env file or create from example"""
        if env_file.exists():
            with open(env_file, 'r') as f:
                return f.read()
        else:
            # Create from example
            example_file = env_file.parent / 'env.example'
            if example_file.exists():
                with open(example_file, 'r') as f:
                    return f.read()
            else:
                return ""

    def update_env_variable(self, content, key, value):
        """Update or add environment variable in content"""
        lines = content.split('\n')
        
        # Find existing variable
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}'
                return '\n'.join(lines)
        
        # Add new variable
        lines.append(f'{key}={value}')
        return '\n'.join(lines)

    def is_ganache_running(self, port):
        """Check if Ganache is running on specified port"""
        try:
            import requests
            response = requests.post(
                f'http://127.0.0.1:{port}',
                json={
                    'jsonrpc': '2.0',
                    'method': 'eth_blockNumber',
                    'params': [],
                    'id': 1
                },
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
