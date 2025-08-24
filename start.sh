#!/bin/bash

# AuthentiCred Startup Script for Railway
set -e

echo "🚀 Starting AuthentiCred..."

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput || echo "⚠️  Migration failed, but continuing..."

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "⚠️  Static collection failed, but continuing..."

# Create superuser if needed
echo "👤 Checking superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@authenticred.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
" || echo "⚠️  Superuser creation failed, but continuing..."

# Start the application
echo "🚀 Starting Gunicorn..."
exec gunicorn AuthentiCred.wsgi:application -c gunicorn.conf.py
