#!/bin/bash

# AuthentiCred Local Development Setup Script
echo "🚀 Setting up AuthentiCred for local development..."

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL status..."
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   On macOS: brew services start postgresql"
    echo "   On Ubuntu: sudo systemctl start postgresql"
    echo "   On Windows: Start PostgreSQL service from Services"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create database if it doesn't exist
echo "🗄️  Creating database 'authenticred_dev'..."
createdb authenticred_dev 2>/dev/null || echo "Database already exists or creation failed"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from env.local..."
    cp env.local .env
    echo "✅ .env file created. Please review and modify if needed."
else
    echo "✅ .env file already exists"
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create superuser
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

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Local development setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Start Redis: brew services start redis (macOS) or sudo systemctl start redis (Linux)"
echo "2. Start Ganache: ganache-cli (if you have it installed)"
echo "3. Run the development server: python manage.py runserver"
echo "4. Visit: http://localhost:8000"
echo "5. Login with: admin/admin123"
echo ""
echo "🔧 Environment:"
echo "- Database: PostgreSQL (authenticred_dev)"
echo "- Cache: Redis (localhost:6379)"
echo "- Blockchain: Ganache (localhost:7545)"
