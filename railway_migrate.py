#!/usr/bin/env python
"""
Railway Migration Script for AuthentiCred
Run this script manually on Railway if migrations don't run automatically.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings for Railway
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings_production')

# Setup Django
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.core.management.base import CommandError

def main():
    print("🚂 Railway Migration Script for AuthentiCred")
    print("=" * 50)
    
    # Check environment
    print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'Unknown')}")
    print(f"Database URL: {os.environ.get('DATABASE_URL', 'Not set')[:50]}...")
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Show current migration status
    print("\n📋 Current migration status:")
    try:
        execute_from_command_line(['manage.py', 'showmigrations'])
    except Exception as e:
        print(f"❌ Could not show migrations: {e}")
    
    # Run migrations
    print("\n🔄 Running migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--noinput', '--verbosity=2'])
        print("✅ Migrations completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    # Show final migration status
    print("\n📋 Final migration status:")
    try:
        execute_from_command_line(['manage.py', 'showmigrations'])
    except Exception as e:
        print(f"❌ Could not show final migration status: {e}")
    
    # Create superuser if needed
    print("\n👤 Checking superuser...")
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@authenticred.com', 'admin123')
            print("✅ Superuser created successfully")
        else:
            print("✅ Superuser already exists")
    except Exception as e:
        print(f"⚠️  Superuser creation failed: {e}")
    
    print("\n✅ Railway migration script completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
