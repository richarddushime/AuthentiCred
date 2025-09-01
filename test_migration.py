#!/usr/bin/env python3
"""
Test Migration Script for AuthentiCred to Heroku
This script tests the migration process without making actual changes.
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
import django
from django.core.management import call_command
from django.conf import settings

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings')
django.setup()

class TestMigrationManager:
    def __init__(self, app_name=None):
        self.app_name = app_name or "authenticred-app"
        self.base_dir = Path(__file__).parent
        self.media_dir = self.base_dir / "media"
        self.fixtures_dir = self.base_dir / "fixtures"
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create fixtures directory if it doesn't exist
        self.fixtures_dir.mkdir(exist_ok=True)
        
    def check_prerequisites(self):
        """Check if all required tools are available"""
        print("🔍 Checking prerequisites...")
        
        # Check Heroku CLI
        try:
            result = subprocess.run(['heroku', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Heroku CLI: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Heroku CLI not found. Please install it first:")
            print("   brew install heroku/brew/heroku")
            print("   or download from: https://devcenter.heroku.com/articles/heroku-cli")
            return False
        
        # Check if logged in to Heroku
        try:
            result = subprocess.run(['heroku', 'auth:whoami'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Logged in as: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            print("❌ Not logged in to Heroku. Please run: heroku login")
            return False
        
        # Check Git
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Git: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git not found. Please install Git first.")
            return False
        
        return True
    
    def export_database_data(self):
        """Export all database data to JSON fixtures"""
        print("\n🗃️ Exporting database data...")
        
        # Get all Django apps
        apps = ['users', 'credentials', 'wallets', 'blockchain']
        
        for app in apps:
            try:
                print(f"📦 Exporting {app} data...")
                fixture_file = self.fixtures_dir / f"{app}_data.json"
                
                # Use dumpdata to export all data from the app
                call_command('dumpdata', app, 
                           output=str(fixture_file),
                           indent=2,
                           natural_foreign=True,
                           natural_primary=True)
                
                # Check file size
                size_mb = fixture_file.stat().st_size / (1024 * 1024)
                print(f"✅ {app}: {size_mb:.2f} MB")
                
            except Exception as e:
                print(f"⚠️ Warning: Could not export {app}: {e}")
        
        # Export all data at once as backup
        try:
            print("📦 Exporting complete database backup...")
            backup_file = self.fixtures_dir / "complete_backup.json"
            call_command('dumpdata', 
                        output=str(backup_file),
                        indent=2,
                        natural_foreign=True,
                        natural_primary=True)
            
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"✅ Complete backup: {size_mb:.2f} MB")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create complete backup: {e}")
    
    def package_media_files(self):
        """Package all media files for upload"""
        print("\n📁 Packaging media files...")
        
        if not self.media_dir.exists():
            print("⚠️ No media directory found")
            return None
        
        # Create media package
        media_package = self.temp_dir / "media_package.zip"
        
        with zipfile.ZipFile(media_package, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.media_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.media_dir)
                    zipf.write(file_path, arcname)
                    
                    # Show progress for large files
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > 1:
                        print(f"📦 Added: {arcname} ({size_mb:.2f} MB)")
        
        size_mb = media_package.stat().st_size / (1024 * 1024)
        print(f"✅ Media package created: {size_mb:.2f} MB")
        
        return media_package
    
    def check_heroku_app(self):
        """Check if Heroku app exists (read-only)"""
        print(f"\n🔍 Checking Heroku app: {self.app_name}")
        
        try:
            result = subprocess.run(['heroku', 'apps:info', '--app', self.app_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ App {self.app_name} already exists")
                return True
            else:
                print(f"ℹ️ App {self.app_name} does not exist (will be created)")
                return False
        except subprocess.CalledProcessError as e:
            print(f"ℹ️ Could not check app status: {e}")
            return False
    
    def check_postgresql(self):
        """Check if PostgreSQL add-on exists (read-only)"""
        print("🗄️ Checking PostgreSQL add-on...")
        
        try:
            result = subprocess.run(['heroku', 'addons:info', 'heroku-postgresql', '--app', self.app_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PostgreSQL add-on already exists")
                return True
            else:
                print("ℹ️ PostgreSQL add-on does not exist (will be created)")
                return False
        except subprocess.CalledProcessError as e:
            print(f"ℹ️ Could not check PostgreSQL status: {e}")
            return False
    
    def show_migration_summary(self):
        """Show what would happen during migration"""
        print("\n📋 Migration Summary")
        print("=" * 50)
        print(f"🎯 Target App: {self.app_name}")
        print(f"🌐 App URL: https://{self.app_name}.herokuapp.com")
        print(f"🗄️ Database: PostgreSQL (essential-0 plan - ~$5/month)")
        print(f"📁 Media Files: {len(list(self.media_dir.rglob('*')))} files")
        print(f"📊 Database Size: {sum(f.stat().st_size for f in self.fixtures_dir.glob('*.json')) / (1024*1024):.2f} MB")
        
        print("\n🚀 What will happen:")
        print("1. Create/update Heroku app")
        print("2. Add PostgreSQL database")
        print("3. Set environment variables")
        print("4. Deploy application code")
        print("5. Run database migrations")
        print("6. Import all data from fixtures")
        print("7. Upload all media files")
        print("8. Create superuser account")
        
        print("\n💰 Estimated costs:")
        print("- PostgreSQL Essential 0: ~$5/month")
        print("- Dyno: Free tier available")
        print("- Storage: Included in dyno limits")
        
        print("\n⚠️ Important notes:")
        print("- This will create a new Heroku app if it doesn't exist")
        print("- All local data will be exported and imported")
        print("- Media files will be uploaded to Heroku")
        print("- Production environment will be configured")
    
    def cleanup(self):
        """Clean up temporary files"""
        print("\n🧹 Cleaning up...")
        
        try:
            shutil.rmtree(self.temp_dir)
            print("✅ Temporary files cleaned up")
        except Exception as e:
            print(f"⚠️ Could not clean up temporary files: {e}")
    
    def run_test(self):
        """Run the test migration process"""
        print("🧪 Testing AuthentiCred to Heroku Migration")
        print("=" * 50)
        print("This is a TEST run - no changes will be made to Heroku")
        print("=" * 50)
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Export database data
            self.export_database_data()
            
            # Package media files
            media_package = self.package_media_files()
            
            # Check Heroku app status
            self.check_heroku_app()
            
            # Check PostgreSQL status
            self.check_postgresql()
            
            # Show migration summary
            self.show_migration_summary()
            
            print("\n✅ Test completed successfully!")
            print("\nTo run the actual migration, use:")
            print(f"   python migrate_to_heroku.py {self.app_name}")
            print("   or")
            print(f"   ./migrate_to_heroku.sh {self.app_name}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
        
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    app_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    if app_name and app_name.startswith('--'):
        print("Usage: python test_migration.py [app_name]")
        print("If no app_name is provided, 'authenticred-app' will be used")
        return
    
    tester = TestMigrationManager(app_name)
    success = tester.run_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
