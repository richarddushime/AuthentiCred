#!/usr/bin/env python
"""
Migration check and run script for AuthentiCred
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings_production')

# Setup Django
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.core.management.base import CommandError

def check_database():
    """Check if database is accessible"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def show_migrations():
    """Show current migration status"""
    try:
        execute_from_command_line(['manage.py', 'showmigrations'])
        return True
    except Exception as e:
        print(f"❌ Could not show migrations: {e}")
        return False

def run_migrations():
    """Run pending migrations"""
    try:
        execute_from_command_line(['manage.py', 'migrate', '--noinput', '--verbosity=2'])
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    print("🔍 AuthentiCred Migration Check")
    print("=" * 40)
    
    # Check database connection
    if not check_database():
        print("❌ Cannot proceed without database connection")
        return False
    
    # Show current migration status
    print("\n📋 Current migration status:")
    show_migrations()
    
    # Run migrations
    print("\n🔄 Running migrations...")
    if run_migrations():
        print("\n📋 Final migration status:")
        show_migrations()
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
