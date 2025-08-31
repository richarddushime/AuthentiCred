# blockchain/management/commands/debug_blockchain.py
from django.core.management.base import BaseCommand
from django.conf import settings
from blockchain.services import BlockchainService
from blockchain.exceptions import BlockchainError
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug blockchain connection and contract status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('🔍 Debugging Blockchain Status...'))
        self.stdout.write('=' * 50)
        
        # Check settings
        self.stdout.write('\n📋 Settings Check:')
        self.stdout.write(f'  Network: {settings.BLOCKCHAIN_NETWORK}')
        self.stdout.write(f'  RPC URL: {settings.BLOCKCHAIN_RPC_URL}')
        self.stdout.write(f'  Chain ID: {getattr(settings, "GANACHE_CHAIN_ID", "Not set")}')
        
        # Check contract addresses
        self.stdout.write('\n📄 Contract Addresses:')
        for contract_name in ['DIDRegistry', 'TrustRegistry', 'CredentialAnchor', 'RevocationRegistry']:
            address = getattr(settings, f'{contract_name.upper()}_ADDRESS', 'Not set')
            self.stdout.write(f'  {contract_name}: {address}')
        
        # Check operator credentials
        self.stdout.write('\n🔑 Operator Credentials:')
        operator_key = settings.BLOCKCHAIN_OPERATOR_KEY
        operator_address = settings.BLOCKCHAIN_OPERATOR_ADDRESS
        self.stdout.write(f'  Key length: {len(operator_key) if operator_key else 0}')
        self.stdout.write(f'  Address: {operator_address}')
        
        # Test blockchain connection
        self.stdout.write('\n🌐 Blockchain Connection Test:')
        try:
            blockchain_service = BlockchainService()
            self.stdout.write(self.style.SUCCESS('  ✅ Blockchain service initialized successfully'))
            
            if verbose:
                self.stdout.write(f'  Chain ID: {blockchain_service.client.chain_id}')
                self.stdout.write(f'  Sender Address: {blockchain_service.client.sender_address}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Blockchain service initialization failed: {str(e)}'))
            return
        
        # Test contract connections
        self.stdout.write('\n📜 Contract Connection Test:')
        contracts_to_test = [
            ('DIDRegistry', 'resolveDID'),
            ('TrustRegistry', 'isIssuerTrusted'),
            ('CredentialAnchor', 'verifyProof'),
            ('RevocationRegistry', 'isRevoked')
        ]
        
        for contract_name, function_name in contracts_to_test:
            try:
                # Test with dummy data
                if function_name == 'resolveDID':
                    result = blockchain_service.client.call_contract_function(
                        contract_name, function_name, 'dummy_did'
                    )
                elif function_name == 'isIssuerTrusted':
                    result = blockchain_service.client.call_contract_function(
                        contract_name, function_name, 'dummy_did'
                    )
                elif function_name == 'verifyProof':
                    result = blockchain_service.client.call_contract_function(
                        contract_name, function_name, '0' * 64
                    )
                elif function_name == 'isRevoked':
                    result = blockchain_service.client.call_contract_function(
                        contract_name, function_name, 'dummy_credential_id'
                    )
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ {contract_name}.{function_name}: OK'))
                if verbose:
                    self.stdout.write(f'    Result: {result}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ {contract_name}.{function_name}: {str(e)}'))
        
        # Test with real data if available
        self.stdout.write('\n🔍 Real Data Test:')
        try:
            from credentials.models import Credential
            from users.models import User
            
            # Test with a real credential
            credential = Credential.objects.first()
            if credential:
                self.stdout.write(f'  Testing with credential: {credential.id}')
                
                # Test credential anchoring
                try:
                    is_anchored = blockchain_service.client.call_contract_function(
                        'CredentialAnchor',
                        'verifyProof',
                        credential.vc_hash
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Credential anchoring check: {is_anchored}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Credential anchoring check failed: {str(e)}'))
                
                # Test issuer verification
                try:
                    issuer_trusted = blockchain_service.is_issuer_registered(credential.issuer.did)
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Issuer verification check: {issuer_trusted}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Issuer verification check failed: {str(e)}'))
                
                # Test revocation check
                try:
                    is_revoked = blockchain_service.is_credential_revoked(str(credential.id))
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Revocation check: {is_revoked}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Revocation check failed: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠️  No credentials found in database'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Real data test failed: {str(e)}'))
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Blockchain debug completed'))
