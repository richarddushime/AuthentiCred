# AuthentiCred/celery.py
from __future__ import absolute_import
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings')

app = Celery('AuthentiCred')

# Explicitly set Redis as the broker and result backend BEFORE loading settings
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    broker_transport='redis',
    result_backend_transport='redis',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_always_eager=False,
)

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

