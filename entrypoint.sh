#!/bin/sh
set -e  # Exit on any error

echo "=== Starting entrypoint script ==="
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "=== Running migrations ==="
python manage.py migrate --noinput 2>&1 || {
    echo "ERROR: Migration failed!"
    exit 1
}

echo "=== Starting server with gunicorn ==="
echo "PORT: ${PORT:-8000}"
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4 --log-level debug
