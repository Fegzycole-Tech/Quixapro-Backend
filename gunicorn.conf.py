"""Gunicorn configuration file for optimized production deployment."""

import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048
workers = int(os.getenv('GUNICORN_WORKERS', 2))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

preload_app = True

worker_tmp_dir = '/dev/shm'

accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

graceful_timeout = 30

proc_name = 'gunicorn_quixapro'

daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None
