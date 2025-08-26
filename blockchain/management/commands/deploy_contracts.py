import json
import os
import shutil
import subprocess
from web3 import Web3
from django.core.management.base import BaseCommand
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
    
    def handle(self, *args, **options):
        skip_deploy = options['skip_deploy']
        skip_abi_update = options['skip_abi_update']
        
        # Paths
        truffle_project_path = os.path.join(settings.BASE_DIR, 'blockchain', 'Authenticred_contracts')
        abis_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abis')
        build_contracts_path = os.path.join(truffle_project_path, 'build', 'contracts')
        
        # Step 1: Update ABIs from Truffle build
        if not skip_abi_update:
            self.stdout.write("🔄 Updating ABIs from Truffle build...")
            
            # Check if Truffle project exists
            if not os.path.exists(truffle_project_path):
                self.stdout.write(self.style.ERROR(f'Truffle project not found at: {truffle_project_path}'))
                return
            
            # Check if build directory exists
            if not os.path.exists(build_contracts_path):
                self.stdout.write(self.style.WARNING('Truffle build directory not found. Running truffle compile...'))
                try:
                    # Run truffle compile
                    subprocess.run(['truffle', 'compile'], cwd=truffle_project_path, check=True, capture_output=True)
                    self.stdout.write(self.style.SUCCESS('Truffle compile completed successfully'))
                except subprocess.CalledProcessError as e:
                    self.stdout.write(self.style.ERROR(f'Truffle compile failed: {e}'))
                    return
                except FileNotFoundError:
                    self.stdout.write(self.style.ERROR('Truffle not found. Please install Truffle globally: npm install -g truffle'))
                    return
            
            # Create ABIs directory if it doesn't exist
            os.makedirs(abis_path, exist_ok=True)
            
            # Empty the ABIs folder
            for file in os.listdir(abis_path):
                file_path = os.path.join(abis_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.stdout.write(f"🗑️  Removed: {file}")
            
            # Copy built contracts to ABIs folder
            contract_files = [
                'DIDRegistry.json',
                'TrustRegistry.json', 
                'CredentialAnchor.json',
                'RevocationRegistry.json'
            ]
            
            copied_count = 0
            for contract_file in contract_files:
                source_path = os.path.join(build_contracts_path, contract_file)
                dest_path = os.path.join(abis_path, contract_file)
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    self.stdout.write(f"📋 Copied: {contract_file}")
                    copied_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  Contract not found: {contract_file}"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Updated {copied_count} ABIs from Truffle build"))
        
        # Step 2: Deploy contracts (if not skipped)
        if not skip_deploy:
            self.stdout.write("\n🚀 Deploying contracts to Ganache...")
            
            # Connect to Ganache (default in Windows app is usually http://127.0.0.1:7545)
            w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
            if not w3.is_connected():
                self.stdout.write(self.style.ERROR('Failed to connect to Ganache. Make sure it\'s running!'))
                return
            
            # Use the first account from Ganache
            account = w3.eth.accounts[0]
            w3.eth.default_account = account
            
            self.stdout.write(f"Using account: {account}")
            
            # Get contract deployment function
            def deploy_contract(contract_name):
                # Load contract ABI from the updated ABIs folder
                abi_path = os.path.join(abis_path, f'{contract_name}.json')
                if not os.path.exists(abi_path):
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
                tx_hash = contract.constructor().transact()
                tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                self.stdout.write(f"✅ {contract_name} deployed successfully!")
                return tx_receipt.contractAddress, abi
            
            # Deploy all contracts
            contracts = {}
            contract_names = ['DIDRegistry', 'TrustRegistry', 'CredentialAnchor', 'RevocationRegistry']
            
            for contract_name in contract_names:
                address, abi = deploy_contract(contract_name)
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
                self.stdout.write(self.style.ERROR('No contracts were deployed successfully'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Operation completed successfully!'))
            