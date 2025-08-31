# blockchain/management/commands/fix_credential_signature.py
from django.core.management.base import BaseCommand
from credentials.models import Credential
from blockchain.utils.crypto import sign_data
import json
from datetime import datetime

class Command(BaseCommand):
    help = 'Fix credential signatures by updating holder DID and re-signing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Fixing Credential Signatures...'))
        self.stdout.write('=' * 50)
        
        credentials = Credential.objects.all()
        fixed_count = 0
        
        for credential in credentials:
            try:
                # Check if credential subject has null ID
                if credential.vc_json.get('credentialSubject', {}).get('id') is None:
                    self.stdout.write(f'  🔧 Fixing credential: {credential.title}')
                    
                    # Update the credential subject with the correct holder DID
                    credential.vc_json['credentialSubject']['id'] = credential.holder.did
                    
                    # Re-sign the credential
                    vc_without_proof = {k: v for k, v in credential.vc_json.items() if k != 'proof'}
                    vc_json_str = json.dumps(vc_without_proof, separators=(',', ':'), sort_keys=True)
                    vc_bytes = vc_json_str.encode('utf-8')
                    
                    # Get the issuer's private key
                    private_key = credential.issuer.wallet.private_key
                    
                    # Clean the private key
                    import re
                    private_key_hex = re.sub(r'[^0-9a-fA-F]', '', private_key)
                    if private_key_hex.startswith('0x'):
                        private_key_hex = private_key_hex[2:]
                    
                    # Sign the credential
                    signature_hex = sign_data(vc_bytes, private_key_hex)
                    
                    # Update the proof
                    credential.vc_json['proof']['jws'] = f"v={signature_hex}"
                    credential.vc_json['proof']['created'] = datetime.utcnow().isoformat() + "Z"
                    
                    # Save the credential
                    credential.save()
                    
                    self.stdout.write(self.style.SUCCESS(f'    ✅ Fixed signature for: {credential.title}'))
                    fixed_count += 1
                else:
                    self.stdout.write(f'  ✅ Credential already has correct ID: {credential.title}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Failed to fix credential {credential.title}: {str(e)}'))
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'📊 Fixed {fixed_count} credentials')
        self.stdout.write(self.style.SUCCESS('✅ Credential signature fix completed'))
