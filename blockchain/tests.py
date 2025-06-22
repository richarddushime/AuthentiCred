# from django.test import TestCase

# # Create your tests here.
# # tests.py
# import os
# import json
# from django.test import TestCase
# from blockchain.services import BlockchainService
# from blockchain.utils import vc_proofs
# from credentials.models import Credential
# from users.models import User, InstitutionProfile

# class BlockchainTestCase(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         # Create institution
#         user = User.objects.create_user(
#             email='university@example.com',
#             password='password',
#             user_type='INSTITUTION'
#         )
#         cls.institution = InstitutionProfile.objects.create(
#             user=user,
#             name='Test University',
#             is_trusted=True
#         )
        
#         # Generate DID keys
#         private_key, public_key = vc_proofs.generate_key_pair()
#         cls.institution_did = 'did:example:university'
#         cls.institution_public_key = public_key
        
#     def test_did_registration(self):
#         # Register DID
#         service = BlockchainService()
#         tx_hash = service.register_did(
#             self.institution_did, 
#             self.institution_public_key.hex()
#         )
        
#         # Check transaction record
#         tx_record = OnChainTransaction.objects.get(tx_hash=tx_hash)
#         self.assertEqual(tx_record.transaction_type, 'DID_REGISTRATION')
        
#         # Verify DID registration (after some delay)
#         # In real test, wait for confirmation
#         registered_key = service.client.call_contract_function(
#             'DIDRegistry',
#             'resolveDID',
#             self.institution_did
#         )
#         self.assertEqual(registered_key, self.institution_public_key.hex())
    
#     def test_credential_lifecycle(self):
#         # Create a test credential
#         credential_data = {
#             '@context': ['https://www.w3.org/2018/credentials/v1'],
#             'type': ['VerifiableCredential', 'UniversityDegreeCredential'],
#             'issuer': self.institution_did,
#             'issuanceDate': '2023-01-01T00:00:00Z',
#             'credentialSubject': {
#                 'id': 'did:example:student123',
#                 'degree': {
#                     'type': 'BachelorDegree',
#                     'name': 'Bachelor of Science'
#                 }
#             }
#         }
        
#         # Sign credential
#         private_key, _ = vc_proofs.generate_key_pair()
#         signed_vc = vc_proofs.sign_json_ld(credential_data, private_key)
        
#         # Create credential in DB
#         credential = Credential.objects.create(
#             vc_json=signed_vc,
#             issuer=self.institution,
#             holder=User.objects.create_user(email='student@example.com', password='password')
#         )
        
#         # Anchor credential hash to blockchain
#         vc_hash = vc_proofs.compute_sha256(json.dumps(signed_vc))
#         service = BlockchainService()
#         tx_hash = service.anchor_credential(vc_hash)
        
#         # Check transaction record
#         tx_record = OnChainTransaction.objects.get(tx_hash=tx_hash)
#         self.assertEqual(tx_record.transaction_type, 'CREDENTIAL_ANCHORING')
        
#         # Verify credential anchoring
#         anchored = service.client.call_contract_function(
#             'CredentialAnchor',
#             'verifyProof',
#             vc_hash
#         )
#         self.assertTrue(anchored)
        
#         # Revoke credential
#         tx_hash = service.revoke_credential(str(credential.id))
#         tx_record = OnChainTransaction.objects.get(tx_hash=tx_hash)
#         self.assertEqual(tx_record.transaction_type, 'CREDENTIAL_REVOCATION')
        
#         # Check revocation status
#         revoked = service.is_credential_revoked(str(credential.id))
#         self.assertTrue(revoked)
    
#     def test_trust_registry(self):
#         service = BlockchainService()
        
#         # Initially should not be trusted
#         trusted = service.is_issuer_registered(self.institution_did)
#         self.assertFalse(trusted)
        
#         # Add to trust registry (admin function)
#         tx_hash = service.client.execute_contract_function(
#             'TrustRegistry',
#             'setIssuerTrustStatus',
#             self.institution_did,
#             True
#         )
        
#         # Now should be trusted
#         trusted = service.is_issuer_registered(self.institution_did)
#         self.assertTrue(trusted)
