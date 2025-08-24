# Gunicorn configuration file for AuthentiCred
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = 1  # Use only 1 worker for debugging
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging - enhanced for debugging
accesslog = "-"
errorlog = "-"
loglevel = "debug"  # Set to debug for more information
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "authenticred"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None

# Preload app for better performance
preload_app = False  # Disable preload for debugging

# Worker timeout for long-running requests (blockchain operations)
timeout = 120

# Enable auto-reload in development
reload = True  # Enable reload for debugging

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Print configuration for debugging
print(f"🔧 Gunicorn Configuration:")
print(f"   Bind: {bind}")
print(f"   Workers: {workers}")
print(f"   Log Level: {loglevel}")
print(f"   Reload: {reload}")
print(f"   Preload App: {preload_app}")
