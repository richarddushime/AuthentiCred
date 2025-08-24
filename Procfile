web: gunicorn AuthentiCred.wsgi:application --bind 0.0.0.0:$PORT --workers 2
release: python manage.py migrate --noinput
