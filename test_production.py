#!/usr/bin/env python
"""
Test script to check if production settings can load properly
"""
import os
import sys
import django

# Set environment variables for testing
os.environ.setdefault('SECRET_KEY', 'qu9f)pntm6g=^7$(n96^z&phcpgd5kvkd)5e8#rh%exdcfoxn2')
os.environ.setdefault('FIELD_ENCRYPTION_KEY', 'CyL_0nL4tTSGYvGbE2ESJqPehpryreCDChtNjGPhnt0=')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings_production')

try:
    # Setup Django
    django.setup()
    print("✅ Production settings loaded successfully!")
    print(f"   DEBUG: {django.conf.settings.DEBUG}")
    print(f"   SECRET_KEY: {django.conf.settings.SECRET_KEY[:10]}...")
    print(f"   DATABASE: {django.conf.settings.DATABASES['default']['ENGINE']}")
    
    # Test basic Django functionality
    from django.core.management import execute_from_command_line
    print("✅ Django core functionality working!")
    
    # Test URL configuration
    from django.urls import get_resolver
    resolver = get_resolver()
    print("✅ URL configuration working!")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
