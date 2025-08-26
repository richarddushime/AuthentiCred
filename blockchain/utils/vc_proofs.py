# blockchain/utils/vc_proofs.py
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
import base58
import hashlib
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der, sigdecode_der


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
    if data is None:
        raise ValueError("Data cannot be None")
    
    # Use hashlib instead of cryptography for simple SHA256
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def sign_json_ld(data_bytes, private_key_hex):
    """
    Sign JSON-LD data using ECDSA with secp256k1 curve
    :param data_bytes: Bytes representation of the JSON-LD data
    :param private_key_hex: Private key in hex format
    :return: Signed JSON-LD document with proof
    """
    try:
        # Ensure private key is in bytes format
        if isinstance(private_key_hex, str):
            private_key_bytes = bytes.fromhex(private_key_hex)
        else:
            private_key_bytes = private_key_hex
            
        # Create signing key
        sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        
        # Create signature
        signature = sk.sign(data_bytes, hashfunc=hashlib.sha256, sigencode=sigencode_der)
        
        # Return signature in hex format
        return signature.hex()
    except Exception as e:
        raise RuntimeError(f"Signing failed: {str(e)}") from e

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
    

def verify_json_ld(data_bytes, signature_hex, public_key_hex):
    """
    Verify JSON-LD signature
    :param data_bytes: Original data in bytes
    :param signature_hex: Signature in hex format
    :param public_key_hex: Public key in hex format
    :return: True if valid, False otherwise
    """
    try:
        # Convert keys to bytes
        if isinstance(public_key_hex, str):
            public_key_bytes = bytes.fromhex(public_key_hex)
        else:
            public_key_bytes = public_key_hex
            
        signature_bytes = bytes.fromhex(signature_hex)
        
        # Create verifying key
        vk = VerifyingKey.from_string(public_key_bytes, curve=SECP256k1)
        
        # Verify signature
        return vk.verify(signature_bytes, data_bytes, hashfunc=hashlib.sha256, sigdecode=sigdecode_der)
    except Exception:
        return False
   