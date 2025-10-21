#!/bin/sh

echo "=== Starting entrypoint script ==="
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "=== Environment variables check ==="
echo "DB_HOST: $DB_HOST"
echo "DB_PORT: $DB_PORT"
echo "POSTGRES_DB: $POSTGRES_DB"
echo "POSTGRES_USER: $POSTGRES_USER"
echo "ALLOWED_HOSTS: $ALLOWED_HOSTS"

echo "=== Running migrations ==="
if ! python manage.py migrate --noinput 2>&1; then
    echo "ERROR: Migration failed! Check database connection."
    exit 1
fi

echo "=== Migrations completed successfully ==="

echo "=== Collecting static files ==="
if ! python manage.py collectstatic --noinput 2>&1; then
    echo "ERROR: Static file collection failed!"
    exit 1
fi

echo "=== Static files collected successfully ==="
echo "=== Starting server with gunicorn ==="
echo "Binding to 0.0.0.0:${PORT:-8000}"
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4 --log-level debug 2>&1
