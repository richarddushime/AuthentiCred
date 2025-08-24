#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting AuthentiCred deployment..."

# Check if we're in a Railway environment
if [ -n "$RAILWAY" ]; then
    echo "📦 Railway environment detected"
    echo "🔧 Using production settings"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build Tailwind CSS
echo "🎨 Building Tailwind CSS..."
if [ -d "theme" ]; then
    cd theme
    npm install --production=false
    npm run build-prod
    cd ..
    echo "✅ Tailwind CSS built successfully"
else:
    echo "⚠️  Theme directory not found, skipping Tailwind build"
fi

# Run Django migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if not exists (only in Railway)
if [ -n "$RAILWAY" ]; then
    echo "👤 Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@authenticred.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('ℹ️  Superuser already exists')
"
fi

# Verify the application can start
echo "🔍 Verifying application configuration..."
python manage.py check --deploy

echo "✅ Deployment setup complete!"
echo "🌐 Application ready to start with gunicorn"
