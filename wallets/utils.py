from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64

def generate_key_pair():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Serialize keys to base64 strings
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    private_str = base64.b64encode(private_bytes).decode('utf-8')
    
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    public_str = base64.b64encode(public_bytes).decode('utf-8')
    
    return private_str, public_str

# # Example usage
# from wallets.utils import generate_key_pair

# private_key, public_key = generate_key_pair()
# wallet = Wallet.objects.create(
#     user=user,
#     private_key=private_key
# )
# # Store public key on user
# user.public_key = public_key
# user.save()
