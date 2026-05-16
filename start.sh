#!/bin/bash
set -e

# Start backend in background
echo "Starting backend on :8001..."
cd /app/backend
API_URL=http://localhost:8001 uvicorn app:app --host 0.0.0.0 --port 8001 --log-level warning &
BACKEND_PID=$!
cd /app

sleep 3

# Start frontend on Hugging Face's expected port
echo "Starting frontend on :7860..."
API_URL=http://localhost:8001 streamlit run /app/frontend/app.py --server.port 7860 --server.headless true

# If frontend stops, kill backend
kill $BACKEND_PID 2>/dev/null