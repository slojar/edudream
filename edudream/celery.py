import os
from decouple import config

from celery import Celery

if config('env', '') == 'prod' or os.getenv('env', 'dev') == 'prod':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edudream.settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edudream.settings.dev')

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('edudream')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

