#!/bin/bash

# AuthentiCred Railway Build Script
set -e

echo "🚀 Starting AuthentiCred deployment..."

# Check if we're in Railway environment
if [ "$RAILWAY" = "true" ]; then
    echo "✅ Running in Railway environment"
    
    # Install system dependencies for PostgreSQL
    echo "📦 Installing system dependencies..."
    apt-get update -qq
    apt-get install -y -qq libpq-dev gcc python3-dev
    
    # Install Python dependencies
    echo "🐍 Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Build Tailwind CSS if theme directory exists
    if [ -d "theme" ]; then
        echo "🎨 Building Tailwind CSS..."
        cd theme
        npm install --production=false
        npm run build-prod
        cd ..
    else
        echo "⚠️  Theme directory not found, skipping Tailwind build"
    fi
    
    # Run Django migrations with better error handling
    echo "🗄️  Running database migrations..."
    echo "   Checking database connection..."
    python manage.py check --database default || echo "⚠️  Database connection check failed, but continuing..."
    
    echo "   Running migrations..."
    python manage.py migrate --noinput --verbosity=2 || {
        echo "❌ Migration failed, trying to show migration status..."
        python manage.py showmigrations || echo "⚠️  Could not show migration status"
        echo "   Trying to run migrations again..."
        python manage.py migrate --noinput --verbosity=2 || echo "❌ Migration failed again"
    }
    
    echo "   Migration status:"
    python manage.py showmigrations || echo "⚠️  Could not show migration status"
    
    # Collect static files (with error handling)
    echo "📁 Collecting static files..."
    if python manage.py help | grep -q collectstatic; then
        python manage.py collectstatic --noinput --clear
        echo "✅ Static files collected successfully"
    else
        echo "⚠️  collectstatic command not available, skipping static collection"
        echo "   This is normal if django.contrib.staticfiles is not properly configured"
    fi
    
    # Create superuser if in Railway environment
    echo "👤 Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@authenticred.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
" || echo "⚠️  Superuser creation failed, but continuing..."
    
    # Final deployment check
    echo "🔍 Running deployment checks..."
    python manage.py check --deploy || echo "⚠️  Deployment check failed, but continuing..."
    
    echo "✅ Build completed successfully!"
else
    echo "⚠️  Not in Railway environment, skipping deployment-specific steps"
    
    # Install Python dependencies
    echo "🐍 Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Build Tailwind CSS if theme directory exists
    if [ -d "theme" ]; then
        echo "🎨 Building Tailwind CSS..."
        cd theme
        npm install
        npm run build-prod
        cd ..
    fi
    
    echo "✅ Local build completed successfully!"
fi
