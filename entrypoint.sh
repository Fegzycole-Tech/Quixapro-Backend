#!/bin/sh

echo "Running migrations..."
python manage.py migrate

echo "Starting server with gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4
