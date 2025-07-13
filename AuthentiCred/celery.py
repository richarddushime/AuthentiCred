# AuthentiCred/celery.py
from __future__ import absolute_import
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings')

app = Celery('AuthentiCred')

# Using a string here prevents serialization issues
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Add the beat schedule here
app.conf.beat_schedule = {
    'monitor-blockchain-transactions': {
        'task': 'blockchain.tasks.monitor_transactions',
        'schedule': 10.0,
    },
    'check-did-confirmations': {
        'task': 'blockchain.tasks.process_did_registration_confirmation',
        'schedule': 300.0,  # 5 minutes
    },
}

