import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pdp_lab_backend.settings")

app = Celery("pdp_lab_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
