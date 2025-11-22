#!/bin/bash

echo "Starting VaultMind Pro..."

# Check and regenerate Skyflow bearer token if needed
echo "Checking Skyflow bearer token..."
python3 check_and_regenerate_token.py || echo "⚠️  Token check failed, continuing anyway..."
echo ""

# Function to kill background processes on exit
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p)
    exit
}

trap cleanup SIGINT SIGTERM

# Check for Redis
if command -v redis-server &> /dev/null; then
    echo "Starting Redis..."
    redis-server &
    REDIS_PID=$!
    sleep 2
    
    echo "Starting Celery Worker..."
    echo "Starting Celery Worker..."
    # Run from project root to ensure relative imports work
    celery -A backend.workers.tasks:celery_app worker --loglevel=info &
else
    echo "WARNING: redis-server not found. Background processing (Celery) will not work."
fi

# Start Backend
echo "Starting Backend (FastAPI)..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend (Vite)..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Wait for all background processes
wait
