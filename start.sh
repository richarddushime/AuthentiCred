#!/bin/bash

# AuthentiCred Startup Script
set -e

echo "🚀 Starting AuthentiCred..."

# Set Railway environment variable
export RAILWAY=true

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "🚀 Starting Gunicorn..."
exec gunicorn AuthentiCred.wsgi:application --bind 0.0.0.0:$PORT --workers 2
