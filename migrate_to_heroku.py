#!/usr/bin/env python3
"""
Comprehensive Migration Script for AuthentiCred to Heroku
This script migrates ALL local database data and media files to Heroku.

Usage:
    python migrate_to_heroku.py [app_name]

Features:
- Exports all database data to JSON fixtures
- Packages all media files
- Sets up Heroku app with PostgreSQL
- Imports data and media files
- Configures environment variables
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

class HerokuMigrationManager:
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
    
    def setup_heroku_app(self):
        """Set up Heroku app with PostgreSQL"""
        print(f"\n🚀 Setting up Heroku app: {self.app_name}")
        
        # Check if app exists, if not create it
        try:
            result = subprocess.run(['heroku', 'apps:info', '--app', self.app_name], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"🏗️ Creating new Heroku app: {self.app_name}")
                subprocess.run(['heroku', 'create', self.app_name], check=True)
            else:
                print(f"✅ App {self.app_name} already exists")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating app: {e}")
            return False
        
        # Add PostgreSQL add-on
        print("🗄️ Adding PostgreSQL add-on...")
        try:
            subprocess.run(['heroku', 'addons:create', 'heroku-postgresql:essential-0', 
                          '--app', self.app_name], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error adding PostgreSQL: {e}")
            return False
        
        # Wait for addon to be provisioned
        print("⏳ Waiting for PostgreSQL to be ready...")
        import time
        time.sleep(15)
        
        # Get the DATABASE_URL
        print("🔗 Getting DATABASE_URL...")
        try:
            result = subprocess.run(['heroku', 'config:get', 'DATABASE_URL', 
                                  '--app', self.app_name], 
                                  capture_output=True, text=True, check=True)
            database_url = result.stdout.strip()
            print(f"✅ DATABASE_URL configured: {database_url[:50]}...")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting DATABASE_URL: {e}")
            return False
        
        # Set environment variables
        print("⚙️ Setting environment variables...")
        try:
            # Generate new secret key
            from django.core.management.utils import get_random_secret_key
            secret_key = get_random_secret_key()
            
            subprocess.run(['heroku', 'config:set', f'SECRET_KEY={secret_key}', 
                          '--app', self.app_name], check=True)
            subprocess.run(['heroku', 'config:set', 'DEBUG=False', 
                          '--app', self.app_name], check=True)
            subprocess.run(['heroku', 'config:set', f'ALLOWED_HOSTS={self.app_name}.herokuapp.com', 
                          '--app', self.app_name], check=True)
            subprocess.run(['heroku', 'config:set', 'HEROKU=true', 
                          '--app', self.app_name], check=True)
            
            # Set field encryption key
            field_key = "4p_Wu4EIAb0GpcHMZYmHfUXZ-EIUve1IBPYKUNH_i8w="
            subprocess.run(['heroku', 'config:set', f'FIELD_ENCRYPTION_KEY={field_key}', 
                          '--app', self.app_name], check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error setting environment variables: {e}")
            return False
        
        return True
    
    def deploy_to_heroku(self):
        """Deploy the app to Heroku"""
        print("\n🚀 Deploying to Heroku...")
        
        try:
            # Add all files
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Commit changes
            commit_message = f"Deploy migration data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            
            # Push to Heroku
            subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
            
            print("✅ Deployment successful!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
            return False
        
        return True
    
    def run_migrations(self):
        """Run database migrations on Heroku"""
        print("\n🗃️ Running database migrations...")
        
        try:
            subprocess.run(['heroku', 'run', 'python', 'manage.py', 'migrate', 
                          '--app', self.app_name], check=True)
            print("✅ Migrations completed!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Migrations failed: {e}")
            return False
        
        return True
    
    def import_data(self):
        """Import data from fixtures to Heroku"""
        print("\n📥 Importing data to Heroku...")
        
        # Upload fixtures to Heroku
        fixtures_zip = self.temp_dir / "fixtures.zip"
        with zipfile.ZipFile(fixtures_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fixture_file in self.fixtures_dir.glob("*.json"):
                zipf.write(fixture_file, fixture_file.name)
        
        # Copy fixtures to Heroku
        try:
            subprocess.run(['heroku', 'run', 'mkdir', '-p', 'fixtures', 
                          '--app', self.app_name], check=True)
            
            # Upload each fixture file
            for fixture_file in self.fixtures_dir.glob("*.json"):
                print(f"📤 Uploading {fixture_file.name}...")
                subprocess.run(['heroku', 'run', '--app', self.app_name, 
                              'bash', '-c', f'cat > fixtures/{fixture_file.name}'], 
                              input=fixture_file.read_bytes(), check=True)
            
            # Import data
            print("📥 Loading data...")
            subprocess.run(['heroku', 'run', 'python', 'manage.py', 'loaddata', 
                          'fixtures/complete_backup.json', '--app', self.app_name], check=True)
            
            print("✅ Data import completed!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Data import failed: {e}")
            return False
        
        return True
    
    def upload_media_files(self, media_package):
        """Upload media files to Heroku"""
        if not media_package:
            print("⚠️ No media package to upload")
            return True
        
        print("\n📁 Uploading media files...")
        
        try:
            # Extract media package on Heroku
            subprocess.run(['heroku', 'run', 'mkdir', '-p', 'media', 
                          '--app', self.app_name], check=True)
            
            # Upload the zip file
            print("📤 Uploading media package...")
            subprocess.run(['heroku', 'run', '--app', self.app_name, 
                          'bash', '-c', 'cat > media_package.zip'], 
                          input=media_package.read_bytes(), check=True)
            
            # Extract on Heroku
            print("📦 Extracting media files...")
            subprocess.run(['heroku', 'run', 'unzip', '-o', 'media_package.zip', 
                          '-d', 'media', '--app', self.app_name], check=True)
            
            # Clean up
            subprocess.run(['heroku', 'run', 'rm', 'media_package.zip', 
                          '--app', self.app_name], check=True)
            
            print("✅ Media files uploaded successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Media upload failed: {e}")
            return False
        
        return True
    
    def create_superuser(self):
        """Create a superuser on Heroku"""
        print("\n👤 Creating superuser...")
        
        try:
            subprocess.run(['heroku', 'run', 'python', 'manage.py', 'createsuperuser', 
                          '--noinput', '--app', self.app_name], check=True)
            print("✅ Superuser created!")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Could not create superuser: {e}")
            print("You can create one manually with: heroku run python manage.py createsuperuser")
    
    def cleanup(self):
        """Clean up temporary files"""
        print("\n🧹 Cleaning up...")
        
        try:
            shutil.rmtree(self.temp_dir)
            print("✅ Temporary files cleaned up")
        except Exception as e:
            print(f"⚠️ Could not clean up temporary files: {e}")
    
    def run_migration(self):
        """Run the complete migration process"""
        print("🚀 Starting AuthentiCred to Heroku Migration")
        print("=" * 50)
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Export database data
            self.export_database_data()
            
            # Package media files
            media_package = self.package_media_files()
            
            # Setup Heroku app
            if not self.setup_heroku_app():
                return False
            
            # Deploy to Heroku
            if not self.deploy_to_heroku():
                return False
            
            # Run migrations
            if not self.run_migrations():
                return False
            
            # Import data
            if not self.import_data():
                return False
            
            # Upload media files
            if not self.upload_media_files(media_package):
                return False
            
            # Create superuser
            self.create_superuser()
            
            print("\n🎉 Migration completed successfully!")
            print(f"🌐 Your app is available at: https://{self.app_name}.herokuapp.com")
            print("\n📊 Useful commands:")
            print(f"   View logs: heroku logs --tail --app {self.app_name}")
            print(f"   Access database: heroku pg:psql --app {self.app_name}")
            print(f"   Run shell: heroku run python manage.py shell --app {self.app_name}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            return False
        
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    app_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    if app_name and app_name.startswith('--'):
        print("Usage: python migrate_to_heroku.py [app_name]")
        print("If no app_name is provided, 'authenticred-app' will be used")
        return
    
    migrator = HerokuMigrationManager(app_name)
    success = migrator.run_migration()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
