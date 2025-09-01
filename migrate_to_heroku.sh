#!/bin/bash

# Comprehensive Migration Script for AuthentiCred to Heroku
# This script migrates ALL local database data and media files to Heroku.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Get app name from command line argument
APP_NAME=${1:-"authenticred-app"}

echo "🚀 Starting AuthentiCred to Heroku Migration"
echo "=================================================="
print_status "Using Heroku app: $APP_NAME"

# Check prerequisites
check_prerequisites() {
    print_status "🔍 Checking prerequisites..."
    
    # Check Heroku CLI
    if ! command -v heroku &> /dev/null; then
        print_error "❌ Heroku CLI not found. Please install it first:"
        echo "   brew install heroku/brew/heroku"
        echo "   or download from: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    print_success "✅ Heroku CLI found"
    
    # Check if logged in to Heroku
    if ! heroku auth:whoami &> /dev/null; then
        print_error "❌ Not logged in to Heroku. Please run: heroku login"
        exit 1
    fi
    print_success "✅ Logged in to Heroku as: $(heroku auth:whoami)"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "❌ Git not found. Please install Git first."
        exit 1
    fi
    print_success "✅ Git found"
    
    # Check if virtual environment is activated
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "⚠️ Virtual environment not activated. Activating .venv..."
        source .venv/bin/activate
    fi
    print_success "✅ Virtual environment activated"
}

# Export database data
export_database_data() {
    print_status "🗃️ Exporting database data..."
    
    # Create fixtures directory
    mkdir -p fixtures
    
    # Export data from each app
    APPS=("users" "credentials" "wallets" "blockchain")
    
    for app in "${APPS[@]}"; do
        print_status "📦 Exporting $app data..."
        if python manage.py dumpdata "$app" --indent=2 --natural-foreign --natural-primary > "fixtures/${app}_data.json" 2>/dev/null; then
            size_mb=$(du -h "fixtures/${app}_data.json" | cut -f1)
            print_success "✅ $app: $size_mb"
        else
            print_warning "⚠️ Could not export $app data"
        fi
    done
    
    # Export complete backup
    print_status "📦 Exporting complete database backup..."
    if python manage.py dumpdata --indent=2 --natural-foreign --natural-primary > "fixtures/complete_backup.json" 2>/dev/null; then
        size_mb=$(du -h "fixtures/complete_backup.json" | cut -f1)
        print_success "✅ Complete backup: $size_mb"
    else
        print_warning "⚠️ Could not create complete backup"
    fi
}

# Package media files
package_media_files() {
    print_status "📁 Packaging media files..."
    
    if [ ! -d "media" ]; then
        print_warning "⚠️ No media directory found"
        return
    fi
    
    # Create media package
    if command -v zip &> /dev/null; then
        zip -r "media_package.zip" media/
        size_mb=$(du -h "media_package.zip" | cut -f1)
        print_success "✅ Media package created: $size_mb"
    else
        print_warning "⚠️ Zip command not found, media files will not be packaged"
    fi
}

# Setup Heroku app
setup_heroku_app() {
    print_status "🚀 Setting up Heroku app: $APP_NAME"
    
    # Check if app exists, if not create it
    if ! heroku apps:info --app "$APP_NAME" &> /dev/null; then
        print_status "🏗️ Creating new Heroku app: $APP_NAME"
        heroku create "$APP_NAME"
    else
        print_success "✅ App $APP_NAME already exists"
    fi
    
    # Add PostgreSQL add-on
    print_status "🗄️ Adding PostgreSQL add-on..."
    if ! heroku addons:info heroku-postgresql --app "$APP_NAME" &> /dev/null; then
        heroku addons:create heroku-postgresql:essential-0 --app "$APP_NAME"
    else
        print_success "✅ PostgreSQL already exists"
    fi
    
    # Wait for addon to be provisioned
    print_status "⏳ Waiting for PostgreSQL to be ready..."
    sleep 15
    
    # Get the DATABASE_URL
    print_status "🔗 Getting DATABASE_URL..."
    DATABASE_URL=$(heroku config:get DATABASE_URL --app "$APP_NAME")
    print_success "✅ DATABASE_URL configured: ${DATABASE_URL:0:50}..."
    
    # Set environment variables
    print_status "⚙️ Setting environment variables..."
    SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    heroku config:set SECRET_KEY="$SECRET_KEY" --app "$APP_NAME"
    heroku config:set DEBUG=False --app "$APP_NAME"
    heroku config:set ALLOWED_HOSTS="$APP_NAME.herokuapp.com" --app "$APP_NAME"
    heroku config:set HEROKU=true --app "$APP_NAME"
    heroku config:set FIELD_ENCRYPTION_KEY="4p_Wu4EIAb0GpcHMZYmHfUXZ-EIUve1IBPYKUNH_i8w=" --app "$APP_NAME"
    
    print_success "✅ Environment variables configured"
}

# Deploy to Heroku
deploy_to_heroku() {
    print_status "🚀 Deploying to Heroku..."
    
    # Add all files
    git add .
    
    # Commit changes
    COMMIT_MSG="Deploy migration data - $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    
    # Push to Heroku
    git push heroku main
    
    print_success "✅ Deployment successful!"
}

# Run migrations
run_migrations() {
    print_status "🗃️ Running database migrations..."
    heroku run python manage.py migrate --app "$APP_NAME"
    print_success "✅ Migrations completed!"
}

# Import data
import_data() {
    print_status "📥 Importing data to Heroku..."
    
    # Create fixtures directory on Heroku
    heroku run mkdir -p fixtures --app "$APP_NAME"
    
    # Upload fixture files
    for fixture_file in fixtures/*.json; do
        if [ -f "$fixture_file" ]; then
            filename=$(basename "$fixture_file")
            print_status "📤 Uploading $filename..."
            heroku run --app "$APP_NAME" bash -c "cat > fixtures/$filename" < "$fixture_file"
        fi
    done
    
    # Import data
    print_status "📥 Loading data..."
    heroku run python manage.py loaddata fixtures/complete_backup.json --app "$APP_NAME"
    
    print_success "✅ Data import completed!"
}

# Upload media files
upload_media_files() {
    if [ ! -f "media_package.zip" ]; then
        print_warning "⚠️ No media package to upload"
        return
    fi
    
    print_status "📁 Uploading media files..."
    
    # Create media directory on Heroku
    heroku run mkdir -p media --app "$APP_NAME"
    
    # Upload the zip file
    print_status "📤 Uploading media package..."
    heroku run --app "$APP_NAME" bash -c "cat > media_package.zip" < "media_package.zip"
    
    # Extract on Heroku
    print_status "📦 Extracting media files..."
    heroku run unzip -o media_package.zip -d media --app "$APP_NAME"
    
    # Clean up
    heroku run rm media_package.zip --app "$APP_NAME"
    
    print_success "✅ Media files uploaded successfully!"
}

# Create superuser
create_superuser() {
    print_status "👤 Creating superuser..."
    
    if heroku run python manage.py createsuperuser --noinput --app "$APP_NAME" 2>/dev/null; then
        print_success "✅ Superuser created!"
    else
        print_warning "⚠️ Could not create superuser automatically"
        echo "You can create one manually with: heroku run python manage.py createsuperuser --app $APP_NAME"
    fi
}

# Cleanup
cleanup() {
    print_status "🧹 Cleaning up..."
    
    # Remove temporary files
    rm -f media_package.zip
    
    print_success "✅ Cleanup completed"
}

# Main migration function
run_migration() {
    # Check prerequisites
    check_prerequisites
    
    # Export database data
    export_database_data
    
    # Package media files
    package_media_files
    
    # Setup Heroku app
    setup_heroku_app
    
    # Deploy to Heroku
    deploy_to_heroku
    
    # Run migrations
    run_migrations
    
    # Import data
    import_data
    
    # Upload media files
    upload_media_files
    
    # Create superuser
    create_superuser
    
    print_success "🎉 Migration completed successfully!"
    echo "🌐 Your app is available at: https://$APP_NAME.herokuapp.com"
    echo ""
    echo "📊 Useful commands:"
    echo "   View logs: heroku logs --tail --app $APP_NAME"
    echo "   Access database: heroku pg:psql --app $APP_NAME"
    echo "   Run shell: heroku run python manage.py shell --app $APP_NAME"
}

# Show usage if help requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [app_name]"
    echo "If no app_name is provided, 'authenticred-app' will be used"
    echo ""
    echo "This script will:"
    echo "1. Export all database data to JSON fixtures"
    echo "2. Package all media files"
    echo "3. Set up Heroku app with PostgreSQL"
    echo "4. Deploy the app"
    echo "5. Import data and media files"
    echo "6. Create a superuser"
    exit 0
fi

# Run the migration
run_migration
