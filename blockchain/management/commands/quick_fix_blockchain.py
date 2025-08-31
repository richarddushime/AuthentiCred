# blockchain/management/commands/quick_fix_blockchain.py
from django.core.management.base import BaseCommand
from django.conf import settings
from web3 import Web3
from credentials.models import Credential
from users.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Quick fix for blockchain state using a funded account'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Quick Fix for Blockchain State...'))
        self.stdout.write('=' * 50)
        
        try:
            w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
            if not w3.is_connected():
                self.stdout.write(self.style.ERROR('❌ Failed to connect to blockchain'))
                return
            
            self.stdout.write(self.style.SUCCESS('✅ Connected to blockchain'))
            
            # Get a funded account
            accounts = w3.eth.accounts
            funded_account = None
            
            for account in accounts[:5]:
                balance = w3.eth.get_balance(account)
                if balance > w3.to_wei(10, 'ether'):
                    funded_account = account
                    balance_eth = w3.from_wei(balance, 'ether')
                    self.stdout.write(f'✅ Using funded account: {account} ({balance_eth} ETH)')
                    break
            
            if not funded_account:
                self.stdout.write(self.style.ERROR('❌ No funded accounts found'))
                return
            
            # Load contract ABIs
            import os
            import json
            
            def load_contract(contract_name):
                abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abis', f'{contract_name}.json')
                with open(abi_path) as f:
                    contract_data = json.load(f)
                
                if isinstance(contract_data, dict) and 'abi' in contract_data:
                    abi = contract_data['abi']
                else:
                    abi = contract_data
                
                address = getattr(settings, f"{contract_name.upper()}_ADDRESS")
                return w3.eth.contract(address=address, abi=abi)
            
            # Load contracts
            trust_registry = load_contract('TrustRegistry')
            credential_anchor = load_contract('CredentialAnchor')
            
            # Register issuers
            issuers = User.objects.filter(issued_credentials__isnull=False).distinct()
            if issuers.count() == 0:
                self.stdout.write(self.style.WARNING('⚠️  No issuers found - skipping issuer registration'))
            else:
                self.stdout.write(f'\n👥 Registering {issuers.count()} issuers...')
                
                for issuer in issuers:
                    if not issuer.did:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Issuer {issuer.username} has no DID'))
                        continue
                    
                    try:
                        # Check if already trusted
                        is_trusted = trust_registry.functions.isIssuerTrusted(issuer.did).call()
                        if is_trusted:
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Issuer {issuer.username} already trusted'))
                        else:
                            # Register as trusted
                            nonce = w3.eth.get_transaction_count(funded_account)
                            tx = trust_registry.functions.setIssuerTrustStatus(issuer.did, True).build_transaction({
                                'chainId': w3.eth.chain_id,
                                'gas': 200000,
                                'gasPrice': w3.to_wei('20', 'gwei'),
                                'nonce': nonce,
                                'from': funded_account,
                            })
                            
                            tx_hash = w3.eth.send_transaction(tx)
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Registered issuer {issuer.username} (tx: {tx_hash.hex()[:10]}...)'))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ Failed to register issuer {issuer.username}: {str(e)}'))
            
            # Anchor credentials
            credentials = Credential.objects.all()
            if credentials.count() == 0:
                self.stdout.write(self.style.WARNING('⚠️  No credentials found - skipping credential anchoring'))
            else:
                self.stdout.write(f'\n📜 Anchoring {credentials.count()} credentials...')
                
                for credential in credentials:
                    try:
                        # Convert hash string to bytes32
                        hash_bytes = bytes.fromhex(credential.vc_hash)
                        
                        # Check if already anchored
                        is_anchored = credential_anchor.functions.verifyProof(hash_bytes).call()
                        if is_anchored:
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Credential {credential.title} already anchored'))
                        else:
                            # Anchor credential
                            nonce = w3.eth.get_transaction_count(funded_account)
                            tx = credential_anchor.functions.storeProof(hash_bytes).build_transaction({
                                'chainId': w3.eth.chain_id,
                                'gas': 200000,
                                'gasPrice': w3.to_wei('20', 'gwei'),
                                'nonce': nonce,
                                'from': funded_account,
                            })
                            
                            tx_hash = w3.eth.send_transaction(tx)
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Anchored credential {credential.title} (tx: {tx_hash.hex()[:10]}...)'))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ Failed to anchor credential {credential.title}: {str(e)}'))
            
            # Test verification if we have credentials
            if credentials.count() > 0:
                self.stdout.write('\n🧪 Testing verification...')
                try:
                    credential = credentials.first()
                    hash_bytes = bytes.fromhex(credential.vc_hash)
                    is_anchored = credential_anchor.functions.verifyProof(hash_bytes).call()
                    issuer_trusted = trust_registry.functions.isIssuerTrusted(credential.issuer.did).call()
                    
                    # Test signature verification
                    from credentials.views import verify_data
                    jws = credential.vc_json['proof']['jws']
                    signature_hex = jws.split('=')[1]
                    vc_without_proof = {k: v for k, v in credential.vc_json.items() if k != 'proof'}
                    vc_json_str = json.dumps(vc_without_proof, separators=(',', ':'), sort_keys=True)
                    vc_bytes = vc_json_str.encode('utf-8')
                    signature_valid = verify_data(vc_bytes, signature_hex, credential.issuer.public_key)
                    
                    self.stdout.write(f'  Credential anchored: {is_anchored}')
                    self.stdout.write(f'  Issuer trusted: {issuer_trusted}')
                    self.stdout.write(f'  Signature valid: {signature_valid}')
                    
                    if is_anchored and issuer_trusted and signature_valid:
                        self.stdout.write(self.style.SUCCESS('  ✅ Verification working correctly!'))
                        self.stdout.write(self.style.SUCCESS('🎉 Blockchain state restored successfully!'))
                    else:
                        self.stdout.write(self.style.WARNING('  ⚠️  Verification still has issues'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Verification test failed: {str(e)}'))
            else:
                self.stdout.write(self.style.SUCCESS('\n✅ Blockchain state ready for new credentials'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Quick fix completed'))
