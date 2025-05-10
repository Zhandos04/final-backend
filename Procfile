web: gunicorn budget_app.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A budget_app worker -l info
beat: celery -A budget_app beat -l info