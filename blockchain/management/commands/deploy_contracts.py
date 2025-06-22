import json
import os
from web3 import Web3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Deploy contracts to Ganache blockchain'
    
    def handle(self, *args, **options):
        # Connect to Ganache (default in Windows app is usually http://127.0.0.1:7545)
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        if not w3.is_connected():
            self.stdout.write(self.style.ERROR('Failed to connect to Ganache. Make sure it\'s running!'))
            return
        
        # Use the first account from Ganache
        account = w3.eth.accounts[0]
        w3.eth.default_account = account
        
        # Get contract deployment function
        def deploy_contract(contract_name):
            # Load contract source
            contract_path = os.path.join(settings.BASE_DIR, 'blockchain', 'contracts', f'{contract_name}.sol')
            with open(contract_path) as f:
                source = f.read()
            
            # Compile contract
            compiled = w3.eth.compile_solidity(source)
            contract_interface = compiled[f'<stdin>:{contract_name}']
            
            # Deploy contract
            contract = w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            tx_hash = contract.constructor().transact()
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            return tx_receipt.contractAddress, contract_interface['abi']
        
        # Deploy all contracts
        contracts = {
            'DIDRegistry': deploy_contract('DIDRegistry'),
            'TrustRegistry': deploy_contract('TrustRegistry'),
            'CredentialAnchor': deploy_contract('CredentialAnchor'),
            'RevocationRegistry': deploy_contract('RevocationRegistry'),
        }
        
        # Save ABIs to files
        os.makedirs(os.path.join(settings.BASE_DIR, 'blockchain', 'abis'), exist_ok=True)
        
        for name, (address, abi) in contracts.items():
            # Save ABI to file
            abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abis', f'{name}.json')
            with open(abi_path, 'w') as f:
                json.dump(abi, f)
            
            self.stdout.write(self.style.SUCCESS(f'{name} deployed to: {address}'))
            self.stdout.write(f'ABI saved to: {abi_path}')
        
        # Output settings to add
        self.stdout.write(self.style.WARNING('\nAdd these to your settings.py:'))
        for name, (address, _) in contracts.items():
            self.stdout.write(f"{name.upper()}_ADDRESS = '{address}'")
            