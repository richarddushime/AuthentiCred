import ecdsa
import hashlib
import os

def generate_key_pair():
    """Generate SECP256k1 key pair in hex format"""
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    
    # Return private key as hex, public key in compressed format as hex
    return sk.to_string().hex(), vk.to_string("compressed").hex()

def generate_public_key_from_private(private_key_hex: str) -> str:
    """Derive public key from private key hex"""
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
    return sk.get_verifying_key().to_string("compressed").hex()

def sign_data(data: bytes, private_key_hex: str) -> str:
    """Sign data using ECDSA (SHA-256) and return signature in hex format"""
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
    signature = sk.sign(data, hashfunc=hashlib.sha256)
    return signature.hex()
