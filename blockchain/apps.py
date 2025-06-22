from django.apps import AppConfig


class BlockchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blockchain'
    
    def ready(self):
        # Start Celery beat when app is ready
        if not hasattr(self, 'celery_beat_started'):
            from .tasks import start_celery_beat
            start_celery_beat()
            self.celery_beat_started = True
            