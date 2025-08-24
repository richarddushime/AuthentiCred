"""
Production settings for AuthentiCred project on Railway.
"""
import os
from pathlib import Path
from .settings import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Force DEBUG to False in production unless explicitly set
if not os.environ.get('DEBUG'):
    DEBUG = False

# Railway automatically sets the PORT environment variable
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',
    '.up.railway.app',
    '*',  # Allow all hosts for now
]

# Add your custom domain if you have one
if os.environ.get('CUSTOM_DOMAIN'):
    ALLOWED_HOSTS.append(os.environ.get('CUSTOM_DOMAIN'))

# Application definition - ensure all apps are loaded
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'encrypted_model_fields',
    'django_celery_results',
    'django_celery_beat',
    'tailwind',
    'theme',
    'blockchain',
    'users',
    'credentials',
    'wallets',
]

# Add WhiteNoise middleware for static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'wallets.middleware.WalletCheckMiddleware',
]

# Database - use SQLite as fallback if DATABASE_URL is not set
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# WhiteNoise configuration for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security settings for production (relaxed for debugging)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # Disabled for debugging
SECURE_HSTS_SECONDS = 0  # Disabled for debugging
SECURE_HSTS_PRELOAD = False  # Disabled for debugging
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = False  # Disabled for debugging
SESSION_COOKIE_SECURE = False  # Disabled for debugging
CSRF_COOKIE_SECURE = False  # Disabled for debugging
X_FRAME_OPTIONS = 'DENY'

# Logging configuration - enhanced for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'gunicorn': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Celery configuration for production
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Blockchain configuration for production
BLOCKCHAIN_NETWORK = os.environ.get('BLOCKCHAIN_NETWORK', 'ganache')
BLOCKCHAIN_RPC_URL = os.environ.get('BLOCKCHAIN_RPC_URL', 'http://127.0.0.1:7545')

# Contract addresses (should be set via environment variables in production)
DIDREGISTRY_ADDRESS = os.environ.get('DIDREGISTRY_ADDRESS', '0x2C20e9cDbb07Be51CF7BC2098eE0B57d7AF3D340')
TRUSTREGISTRY_ADDRESS = os.environ.get('TRUSTREGISTRY_ADDRESS', '0x140e19394017a90fd6f3f6745A35077Cd3F85dEB')
CREDENTIALANCHOR_ADDRESS = os.environ.get('CREDENTIALANCHOR_ADDRESS', '0x0e90921CA3D72e62B06Ecbfb56d0fcEEe04E7cc1')
REVOCATIONREGISTRY_ADDRESS = os.environ.get('REVOCATIONREGISTRY_ADDRESS', '0x397d90a8D731cC2b70af1c4Ca700bAf5530f339A')

# Blockchain operator credentials (should be set via environment variables)
BLOCKCHAIN_OPERATOR_KEY = os.environ.get('BLOCKCHAIN_OPERATOR_KEY', '0x062f69a9da3236435b0f6c3bda1cc7f3a7d7c716f2bfd0283202cc6b258f8d38')
BLOCKCHAIN_OPERATOR_ADDRESS = os.environ.get('BLOCKCHAIN_OPERATOR_ADDRESS', '0x5794777802033929F19C1a901cc2D460480D76f6')

# Field encryption key (should be set via environment variable)
FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY')
if not FIELD_ENCRYPTION_KEY:
    raise ValueError("FIELD_ENCRYPTION_KEY environment variable is required in production")

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    }
}

# Print startup information
print(f"🚀 AuthentiCred Production Settings Loaded")
print(f"   DEBUG: {DEBUG}")
print(f"   ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"   DATABASE: {DATABASES['default']['ENGINE']}")
print(f"   STATIC_ROOT: {STATIC_ROOT}")
