#!/bin/bash

# Heroku Database Setup Script for AuthentiCred
echo "🚀 Setting up Heroku Database for AuthentiCred"

# Check if Heroku CLI is available
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "   brew install heroku/brew/heroku"
    echo "   or download from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "🔐 Please login to Heroku first:"
    echo "   heroku login"
    exit 1
fi

# Get app name (you can change this)
APP_NAME=${1:-"authenticred-app"}

echo "📱 Using Heroku app: $APP_NAME"

# Check if app exists, if not create it
if ! heroku apps:info --app $APP_NAME &> /dev/null; then
    echo "🏗️  Creating new Heroku app: $APP_NAME"
    heroku create $APP_NAME
else
    echo "✅ App $APP_NAME already exists"
fi

# Add PostgreSQL add-on
echo "🗄️  Adding PostgreSQL add-on..."
heroku addons:create heroku-postgresql:mini --app $APP_NAME

# Wait a moment for the addon to be provisioned
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Get the DATABASE_URL
echo "🔗 Getting DATABASE_URL..."
DATABASE_URL=$(heroku config:get DATABASE_URL --app $APP_NAME)
echo "✅ DATABASE_URL configured: ${DATABASE_URL:0:50}..."

# Set other required environment variables
echo "⚙️  Setting environment variables..."
heroku config:set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" --app $APP_NAME
heroku config:set DEBUG=False --app $APP_NAME
heroku config:set ALLOWED_HOSTS="$APP_NAME.herokuapp.com" --app $APP_NAME

# Deploy the app
echo "🚀 Deploying to Heroku..."
git add .
git commit -m "Configure for Heroku deployment"
git push heroku main

# Run migrations
echo "🗃️  Running database migrations..."
heroku run python manage.py migrate --app $APP_NAME

# Create superuser (optional)
echo "👤 Would you like to create a superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    heroku run python manage.py createsuperuser --app $APP_NAME
fi

echo "🎉 Setup complete! Your app is available at:"
echo "   https://$APP_NAME.herokuapp.com"
echo ""
echo "📊 To view logs:"
echo "   heroku logs --tail --app $APP_NAME"
echo ""
echo "🗄️  To access database:"
echo "   heroku pg:psql --app $APP_NAME"
