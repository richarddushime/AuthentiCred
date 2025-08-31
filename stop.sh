#!/bin/bash

# AuthentiCred Stop Script
# ========================

echo "🛑 Stopping AuthentiCred Services"
echo "================================"

# Stop Django server
echo "🌐 Stopping Django server..."
pkill -f "manage.py runserver" 2>/dev/null || echo "  Django server not running"

# Stop Celery worker
echo "🐛 Stopping Celery worker..."
pkill -f "celery worker" 2>/dev/null || echo "  Celery worker not running"

# Stop Celery beat
echo "⏰ Stopping Celery beat..."
pkill -f "celery beat" 2>/dev/null || echo "  Celery beat not running"

# Stop Ganache
echo "🔗 Stopping Ganache..."
pkill -f "ganache" 2>/dev/null || echo "  Ganache not running"

# Stop MkDocs documentation server
echo "📚 Stopping MkDocs documentation server..."
if [ -f ".mkdocs.pid" ]; then
    MKDOCS_PID=$(cat .mkdocs.pid)
    if kill -0 $MKDOCS_PID 2>/dev/null; then
        kill $MKDOCS_PID
        echo "  MkDocs stopped (PID: $MKDOCS_PID)"
    else
        echo "  MkDocs PID file exists but process not running"
    fi
    rm -f .mkdocs.pid
else
    echo "  MkDocs PID file not found"
fi

# Also try to stop any remaining MkDocs processes
pkill -f "mkdocs serve" 2>/dev/null || echo "  No MkDocs processes found"

# Stop Redis container
echo "🔴 Stopping Redis..."
docker stop authenticred-redis 2>/dev/null || echo "  Redis container not running"
docker rm authenticred-redis 2>/dev/null || echo "  Redis container already removed"

echo "✅ All AuthentiCred services stopped"
