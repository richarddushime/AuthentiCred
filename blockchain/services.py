# Core blockchain operations
# blockchain/services.py
import json
import logging
from web3 import Web3
from django.conf import settings
from .exceptions import BlockchainError
from .models import OnChainTransaction

logger = logging.getLogger(__name__)

class BlockchainService:
    CONTRACT_ABIS = {
        'DIDRegistry': 'DIDRegistry.json',
        'TrustRegistry': 'TrustRegistry.json',
        'CredentialAnchor': 'CredentialAnchor.json',
        'RevocationRegistry': 'RevocationRegistry.json',
    }
    
    CONTRACT_ADDRESSES = {
        'DIDRegistry': settings.DIDREGISTRY_ADDRESS,
        'TrustRegistry': settings.TRUSTREGISTRY_ADDRESS,
        'CredentialAnchor': settings.CREDENTIALANCHOR_ADDRESS,
        'RevocationRegistry': settings.REVOCATIONREGISTRY_ADDRESS,
    }
    
    def __init__(self, client=None):
        self.client = client or self.get_default_client()
    
    def get_default_client(self):
        if settings.BLOCKCHAIN_NETWORK == 'ganache':
            from .clients.ganache import GanacheClient
            return GanacheClient()
        else:
            raise BlockchainError("Unsupported blockchain network")
    
    def register_did(self, did, public_key):
        try:
            tx_hash = self.client.execute_contract_function(
                'DIDRegistry',
                'registerDID',
                did,
                public_key
            )
            self._create_transaction_record(tx_hash, 'DID_REGISTRATION', did=did)
            return tx_hash
        except Exception as e:
            logger.error(f"DID registration failed: {str(e)}")
            raise BlockchainError(f"DID registration failed: {str(e)}") from e
    
    def anchor_credential(self, vc_hash):
        try:
            tx_hash = self.client.execute_contract_function(
                'CredentialAnchor',
                'storeProof',
                vc_hash
            )
            self._create_transaction_record(tx_hash, 'CREDENTIAL_ANCHORING', vc_hash=vc_hash)
            return tx_hash
        except Exception as e:
            logger.error(f"Credential anchoring failed: {str(e)}")
            raise BlockchainError(f"Credential anchoring failed: {str(e)}") from e
    
    def revoke_credential(self, credential_id):
        try:
            tx_hash = self.client.execute_contract_function(
                'RevocationRegistry',
                'revokeCredential',
                credential_id
            )
            self._create_transaction_record(tx_hash, 'CREDENTIAL_REVOCATION', credential_id=credential_id)
            return tx_hash
        except Exception as e:
            logger.error(f"Credential revocation failed: {str(e)}")
            raise BlockchainError(f"Credential revocation failed: {str(e)}") from e
    
    def is_issuer_registered(self, did):
        try:
            return self.client.call_contract_function(
                'TrustRegistry',
                'isIssuerTrusted',
                did
            )
        except Exception as e:
            logger.error(f"Issuer check failed: {str(e)}")
            raise BlockchainError(f"Issuer check failed: {str(e)}") from e
    
    def is_credential_revoked(self, credential_id):
        try:
            return self.client.call_contract_function(
                'RevocationRegistry',
                'isRevoked',
                credential_id
            )
        except Exception as e:
            logger.error(f"Revocation check failed: {str(e)}")
            raise BlockchainError(f"Revocation check failed: {str(e)}") from e
    
    def _create_transaction_record(self, tx_hash, tx_type, **kwargs):
        OnChainTransaction.objects.create(
            tx_hash=tx_hash,
            status='PENDING',
            transaction_type=tx_type,
            metadata=kwargs
        )

    def verify_credential(self, credential):
        """Comprehensive credential verification"""
        results = {
            'anchored': False,
            'issuer_trusted': False,
            'not_revoked': False,
            'signature_valid': False
        }
        
        try:
            # Verify anchoring
            results['anchored'] = self.client.call_contract_function(
                'CredentialAnchor',
                'verifyProof',
                credential.vc_hash
            )
            
            # Verify issuer
            results['issuer_trusted'] = self.is_issuer_registered(credential.issuer.did)
            
            # Verify revocation
            results['not_revoked'] = not self.is_credential_revoked(str(credential.id))
            
            # Verify signature (pseudocode - implement based on your crypto)
            # results['signature_valid'] = verify_signature(credential.vc_json)
            
        except Exception as e:
            logger.error(f"Credential verification failed: {str(e)}")
        
        return results
    
