#!/usr/bin/env sh
set -e

python manage.py migrate
python manage.py seed_initial_data
python manage.py collectstatic --noinput

if [ "$RUN_MODE" = "daphne" ]; then
  daphne -b 0.0.0.0 -p 8001 config.asgi:application
elif [ "$RUN_MODE" = "worker" ]; then
  celery -A config worker -l info
elif [ "$RUN_MODE" = "beat" ]; then
  celery -A config beat -l info
else
  gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
fi
