"""
Production settings for AuthentiCred project on Railway.
"""
import os
from pathlib import Path
from .settings import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'zp-f+3iaol4+xcgnb=da6l-$!pjcai=!8r$0w!wmlg-+49cqh&')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Railway automatically sets the PORT environment variable
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',
    '.up.railway.app',
]

# Add your custom domain if you have one
if os.environ.get('CUSTOM_DOMAIN'):
    ALLOWED_HOSTS.append(os.environ.get('CUSTOM_DOMAIN'))

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

# Database
# Railway provides DATABASE_URL environment variable
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
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

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_PRELOAD = True
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Logging configuration
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
    },
}

# Celery configuration for production
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Blockchain configuration for production
# You may want to use different blockchain networks for production
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
FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY', b'4p_Wu4EIAb0GpcHMZYmHfUXZ-EIUve1IBPYKUNH_i8w=')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    }
}
