# blockchain/utils/vc_proofs.py
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
import base58

def generate_key_pair():
    """Generate Ed25519 key pair for DIDs"""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Serialize keys
    private_bytes = private_key.private_bytes(
        Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption()
    )
    
    public_bytes = public_key.public_bytes(
        Encoding.Raw,
        PublicFormat.Raw
    )
    
    return private_bytes, public_bytes

def compute_sha256(data: str) -> str:
    """Compute SHA256 hash of a string"""
    return hashes.Hash(hashes.SHA256()).update(data.encode()).finalize().hex()

def sign_json_ld(credential, private_key_bytes):
    """Sign a JSON-LD credential using Ed25519"""
    # Create a copy without existing proof
    credential = credential.copy()
    if 'proof' in credential:
        del credential['proof']
    
    # Canonicalize the document
    canonical_doc = json.dumps(credential, sort_keys=True, separators=(',', ':'))
    
    # Sign the document
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    signature = private_key.sign(canonical_doc.encode('utf-8'))
    
    # Add proof to credential
    credential['proof'] = {
        'type': 'Ed25519Signature2020',
        'created': datetime.utcnow().isoformat() + 'Z',
        'proofPurpose': 'assertionMethod',
        'verificationMethod': credential['issuer'],
        'proofValue': base58.b58encode(signature).decode('utf-8')
    }
    
    return credential

def verify_json_ld_signature(credential, public_key_bytes):
    """Verify a JSON-LD signature"""
    if 'proof' not in credential:
        return False
        
    proof = credential['proof'].copy()
    credential_no_proof = credential.copy()
    del credential_no_proof['proof']
    
    # Canonicalize the document
    canonical_doc = json.dumps(credential_no_proof, sort_keys=True, separators=(',', ':'))
    
    # Get signature
    signature = base58.b58decode(proof['proofValue'])
    
    # Verify signature
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
    try:
        public_key.verify(signature, canonical_doc.encode('utf-8'))
        return True
    except:
        return False
    