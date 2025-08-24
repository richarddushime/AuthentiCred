#!/bin/bash

# AuthentiCred Startup Script for Railway
set -e

echo "🚀 Starting AuthentiCred..."
echo "Environment: $RAILWAY_ENVIRONMENT"
echo "Port: $PORT"
echo "Database URL: ${DATABASE_URL:0:50}..."
echo "DEBUG: $DEBUG"
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "FIELD_ENCRYPTION_KEY: ${FIELD_ENCRYPTION_KEY:0:10}..."

# Check if we're in Railway
if [ "$RAILWAY" = "true" ]; then
    echo "✅ Running in Railway environment"
else
    echo "⚠️  Not in Railway environment"
fi

# Test database connection first
echo "🔍 Testing database connection..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings_production')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
    print('✅ Database connection successful')
" || {
    echo "❌ Database connection failed"
    echo "⚠️  Continuing anyway..."
}

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput --verbosity=2 || {
    echo "❌ Migration failed"
    echo "⚠️  Continuing anyway..."
}

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear || {
    echo "❌ Static collection failed"
    echo "⚠️  Continuing anyway..."
}

# Create superuser if needed
echo "👤 Checking superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@authenticred.com', 'admin123')
    print('✅ Superuser created successfully')
else:
    print('✅ Superuser already exists')
" || {
    echo "❌ Superuser creation failed"
    echo "⚠️  Continuing anyway..."
}

# Test Django application
echo "🧪 Testing Django application..."
python manage.py check --deploy || {
    echo "❌ Django check failed"
    echo "⚠️  Continuing anyway..."
}

# Show final status
echo "📋 Final status:"
echo "   - Port: $PORT"
echo "   - Database: ${DATABASE_URL:0:30}..."
echo "   - Environment: $RAILWAY_ENVIRONMENT"
echo "   - DEBUG: $DEBUG"

# Start the application
echo "🚀 Starting Gunicorn on port $PORT..."
echo "   Command: gunicorn AuthentiCred.wsgi:application -c gunicorn.conf.py"
echo "   Debug mode: $DEBUG"
exec gunicorn AuthentiCred.wsgi:application -c gunicorn.conf.py
