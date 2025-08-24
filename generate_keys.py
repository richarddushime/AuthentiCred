#!/usr/bin/env python3
"""
Key generation script for AuthentiCred
Generates secure keys for Django and encryption
"""

import os
import sys

def generate_django_secret_key():
    """Generate a Django secret key"""
    try:
        from django.core.management.utils import get_random_secret_key
        return get_random_secret_key()
    except ImportError:
        # Fallback if Django is not available
        import secrets
        import string
        chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        return ''.join(secrets.choice(chars) for _ in range(50))

def generate_encryption_key():
    """Generate a Fernet encryption key"""
    try:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    except ImportError:
        # Fallback if cryptography is not available
        import secrets
        import base64
        key = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(key).decode()

def main():
    print("🔐 AuthentiCred Key Generator")
    print("=" * 40)
    
    # Generate Django secret key
    print("\n📝 Django Secret Key:")
    django_key = generate_django_secret_key()
    print(f"SECRET_KEY={django_key}")
    
    # Generate encryption key
    print("\n🔒 Field Encryption Key:")
    encryption_key = generate_encryption_key()
    print(f"FIELD_ENCRYPTION_KEY={encryption_key}")
    
    print("\n✅ Keys generated successfully!")
    print("\n💡 Copy these keys to your environment variables:")
    print("   - For local development: .env file")
    print("   - For Railway: Environment variables in dashboard")
    
    # Save to file option
    save = input("\n💾 Save to keys.txt? (y/n): ").lower().strip()
    if save == 'y':
        with open('keys.txt', 'w') as f:
            f.write(f"# Generated keys for AuthentiCred\n")
            f.write(f"# Generated on: {os.popen('date').read().strip()}\n\n")
            f.write(f"SECRET_KEY={django_key}\n")
            f.write(f"FIELD_ENCRYPTION_KEY={encryption_key}\n")
        print("✅ Keys saved to keys.txt")
        print("⚠️  Remember to delete keys.txt after copying the keys!")

if __name__ == "__main__":
    main()
