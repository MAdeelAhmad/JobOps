"""
Celery configuration for jobops project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobOps.settings')

app = Celery('jobOps')

# Load task modules from all registered Django apps.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'check-overdue-jobs-daily': {
        'task': 'ops.tasks.check_overdue_jobs',
        'schedule': crontab(hour=0, minute=0),
    },
    'send-daily-task-reminders': {
        'task': 'ops.tasks.send_daily_task_reminder',
        'schedule': crontab(hour=7, minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')