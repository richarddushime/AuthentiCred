#!/usr/bin/env python
"""
Minimal test to check if Django can start
"""
import os
import sys
import django

# Set environment variables for testing
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('FIELD_ENCRYPTION_KEY', 'test-encryption-key-for-testing-only')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings_production')

try:
    print("🔍 Testing Django startup...")
    
    # Setup Django
    django.setup()
    print("✅ Django setup successful!")
    
    # Test basic imports
    from django.conf import settings
    print(f"✅ Settings loaded: DEBUG={settings.DEBUG}")
    
    # Test URL configuration
    from django.urls import get_resolver
    resolver = get_resolver()
    print("✅ URL resolver working!")
    
    # Test basic view
    from django.http import HttpResponse
    print("✅ HTTP response working!")
    
    print("✅ All basic Django functionality working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
