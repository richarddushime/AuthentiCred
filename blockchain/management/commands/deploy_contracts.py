#!/usr/bin/env python3
"""
Django management command for contract deployment
================================================

This command provides comprehensive contract deployment functionality:
1. Copies JSON files from Truffle build to abis folder
2. Deploys contracts using Truffle or direct Web3 deployment
3. Updates .env file with contract addresses
4. Generates operator account credentials

Usage:
    python manage.py deploy_contracts [options]

Options:
    --skip-deploy      Skip contract deployment and only update ABIs
    --skip-abi-update  Skip ABI update and only deploy contracts
    --skip-env-update  Skip updating .env file
    --use-truffle      Use Truffle for deployment (default: direct Web3)
    --ganache-port     Ganache port (default: 8545)
    --network          Network name (default: development)
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from web3 import Web3
from eth_account import Account
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Deploy contracts to Ganache blockchain and update ABIs from Truffle build'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-deploy',
            action='store_true',
            help='Skip contract deployment and only update ABIs from Truffle build',
        )
        parser.add_argument(
            '--skip-abi-update',
            action='store_true',
            help='Skip ABI update and only deploy contracts',
        )
        parser.add_argument(
            '--skip-env-update',
            action='store_true',
            help='Skip updating .env file with contract addresses',
        )
        parser.add_argument(
            '--use-truffle',
            action='store_true',
            help='Use Truffle for deployment (default: direct Web3 deployment)',
        )
        parser.add_argument(
            '--ganache-port',
            type=int,
            default=8545,
            help='Ganache port (default: 8545)',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='development',
            help='Network name (default: development)',
        )
    
    def handle(self, *args, **options):
        skip_deploy = options['skip_deploy']
        skip_abi_update = options['skip_abi_update']
        skip_env_update = options['skip_env_update']
        use_truffle = options['use_truffle']
        ganache_port = options['ganache_port']
        network = options['network']
        
        # Paths
        base_dir = Path(settings.BASE_DIR)
        truffle_project_path = base_dir / 'blockchain' / 'Authenticred_contracts'
        abis_path = base_dir / 'blockchain' / 'abis'
        build_contracts_path = truffle_project_path / 'build' / 'contracts'
        env_file = base_dir / '.env'
        
        self.stdout.write("🚀 AuthentiCred Contract Deployment")
        self.stdout.write("=" * 50)
        
        # Step 1: Update ABIs from Truffle build
        if not skip_abi_update:
            self.update_abis(truffle_project_path, abis_path, build_contracts_path)
        
        # Step 2: Deploy contracts
        if not skip_deploy:
            if use_truffle:
                self.deploy_with_truffle(truffle_project_path, ganache_port)
            else:
                self.deploy_with_web3(abis_path, ganache_port, network)
        
        # Step 3: Update .env file with contract addresses
        if not skip_env_update:
            self.update_env_file(env_file, truffle_project_path)
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Contract deployment completed successfully!'))
    
    def update_abis(self, truffle_project_path, abis_path, build_contracts_path):
        """Update ABIs from Truffle build"""
        self.stdout.write("🔄 Updating ABIs from Truffle build...")
        
        # Check if Truffle project exists
        if not truffle_project_path.exists():
            raise CommandError(f'Truffle project not found at: {truffle_project_path}')
        
        # Check if build directory exists
        if not build_contracts_path.exists():
            self.stdout.write(self.style.WARNING('Truffle build directory not found. Running truffle compile...'))
            try:
                # Run truffle compile
                subprocess.run(['truffle', 'compile'], cwd=truffle_project_path, check=True, capture_output=True)
                self.stdout.write(self.style.SUCCESS('Truffle compile completed successfully'))
            except subprocess.CalledProcessError as e:
                raise CommandError(f'Truffle compile failed: {e}')
            except FileNotFoundError:
                raise CommandError('Truffle not found. Please install Truffle globally: npm install -g truffle')
        
        # Create ABIs directory if it doesn't exist
        abis_path.mkdir(parents=True, exist_ok=True)
        
        # Empty the ABIs folder
        for file in abis_path.iterdir():
            if file.is_file():
                file.unlink()
                self.stdout.write(f"🗑️  Removed: {file.name}")
        
        # Copy built contracts to ABIs folder
        contract_files = [
            'DIDRegistry.json',
            'TrustRegistry.json', 
            'CredentialAnchor.json',
            'RevocationRegistry.json'
        ]
        
        copied_count = 0
        for contract_file in contract_files:
            source_path = build_contracts_path / contract_file
            dest_path = abis_path / contract_file
            
            if source_path.exists():
                shutil.copy2(source_path, dest_path)
                self.stdout.write(f"📋 Copied: {contract_file}")
                copied_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Contract not found: {contract_file}"))
        
        self.stdout.write(self.style.SUCCESS(f"✅ Updated {copied_count} ABIs from Truffle build"))
    
    def deploy_with_truffle(self, truffle_project_path, ganache_port):
        """Deploy contracts using Truffle"""
        self.stdout.write(f"\n🚀 Deploying contracts with Truffle (port: {ganache_port})...")
        
        # Check if Ganache is running
        if not self.is_ganache_running(ganache_port):
            raise CommandError(f'Ganache is not running on port {ganache_port}. Please start Ganache first.')
        
        # Update truffle-config.js with correct port
        self.update_truffle_config(truffle_project_path, ganache_port)
        
        # Run Truffle deployment
        try:
            cmd = ['truffle', 'migrate', '--reset', '--network', 'development']
            result = subprocess.run(
                cmd,
                cwd=truffle_project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.stdout.write('✅ Contracts deployed successfully with Truffle')
            self.stdout.write(result.stdout)
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Truffle deployment failed: {e.stderr}'))
            raise CommandError('Truffle deployment failed')
    
    def deploy_with_web3(self, abis_path, ganache_port, network):
        """Deploy contracts using direct Web3"""
        self.stdout.write(f"\n🚀 Deploying contracts with Web3 (port: {ganache_port})...")
        
        # Connect to Ganache
        w3 = Web3(Web3.HTTPProvider(f'http://127.0.0.1:{ganache_port}'))
        if not w3.is_connected():
            raise CommandError(f'Failed to connect to Ganache on port {ganache_port}. Make sure it\'s running!')
        
        # Use the first account from Ganache
        account = w3.eth.accounts[0]
        w3.eth.default_account = account
        
        self.stdout.write(f"Using account: {account}")
        
        # Deploy all contracts
        contracts = {}
        contract_names = ['DIDRegistry', 'TrustRegistry', 'CredentialAnchor', 'RevocationRegistry']
        
        for contract_name in contract_names:
            address, abi = self.deploy_contract(w3, abis_path, contract_name)
            if address and abi:
                contracts[contract_name] = (address, abi)
        
        # Output deployment results
        if contracts:
            self.stdout.write(self.style.SUCCESS('\n📋 Deployment Summary:'))
            for name, (address, _) in contracts.items():
                self.stdout.write(f"  {name}: {address}")
            
            # Output settings to add
            self.stdout.write(self.style.WARNING('\n📝 Add these to your settings.py:'))
            for name, (address, _) in contracts.items():
                self.stdout.write(f"{name.upper()}_ADDRESS = '{address}'")
        else:
            raise CommandError('No contracts were deployed successfully')
    
    def deploy_contract(self, w3, abis_path, contract_name):
        """Deploy a single contract"""
        # Load contract ABI from the updated ABIs folder
        abi_path = abis_path / f'{contract_name}.json'
        if not abi_path.exists():
            self.stdout.write(self.style.ERROR(f'ABI not found for {contract_name}. Run with --skip-deploy to update ABIs first.'))
            return None, None
        
        with open(abi_path, 'r') as f:
            contract_data = json.load(f)
        
        # Get ABI and bytecode from the compiled contract
        abi = contract_data['abi']
        bytecode = contract_data['bytecode']
        
        # Deploy contract
        contract = w3.eth.contract(
            abi=abi,
            bytecode=bytecode
        )
        
        self.stdout.write(f"Deploying {contract_name}...")
        try:
            tx_hash = contract.constructor().transact()
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.stdout.write(f"✅ {contract_name} deployed successfully!")
            return tx_receipt.contractAddress, abi
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to deploy {contract_name}: {e}"))
            return None, None
    
    def update_truffle_config(self, truffle_project_path, ganache_port):
        """Update truffle-config.js with correct Ganache port"""
        config_file = truffle_project_path / 'truffle-config.js'
        
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
        
        self.stdout.write(f"  ✅ Updated truffle-config.js with port {ganache_port}")
    
    def update_env_file(self, env_file, truffle_project_path):
        """Update .env file with contract addresses"""
        self.stdout.write('⚙️  Updating .env file with contract addresses...')
        
        # Read contract addresses from Truffle build
        addresses = self.get_contract_addresses(truffle_project_path)
        
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
    
    def get_contract_addresses(self, truffle_project_path):
        """Extract contract addresses from Truffle build"""
        addresses = {}
        
        # Read addresses from build artifacts
        build_dir = truffle_project_path / 'build' / 'contracts'
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
            