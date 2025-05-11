import os
from celery import Celery

# установить переменную окружения для настроек проекта

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_app.settings')

app = Celery('budget_app')

# Загрузка настроек из файла settings.py, используя префикс 'CELERY_'

app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение и регистрация задач из всех приложений

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')