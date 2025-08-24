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

# Simple Django check
echo "🧪 Testing Django application..."
python manage.py check || {
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
