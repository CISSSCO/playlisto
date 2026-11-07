#!/bin/bash

echo "🚀 Starting Playlisto..."

ROOT_DIR=$(pwd)
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"
PID_FILE="$ROOT_DIR/playlisto.pid"

mkdir -p "$LOG_DIR"

########################################
# Start Backend
########################################

echo "🔹 Starting Backend..."

cd "$BACKEND_DIR" || exit 1

if [ -d ".playlisto" ]; then
  source .playlisto/bin/activate
elif [ -d ".venv" ]; then
  source .venv/bin/activate
fi

nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  > "$LOG_DIR/backend.log" 2>&1 &

BACKEND_PID=$!

########################################
# Start Frontend
########################################

echo "🔹 Starting Frontend..."

cd "$FRONTEND_DIR" || exit 1

nohup npm run dev \
  > "$LOG_DIR/frontend.log" 2>&1 &

FRONTEND_PID=$!

########################################
# Save PIDs
########################################

echo "$BACKEND_PID $FRONTEND_PID" > "$PID_FILE"

########################################
# Output
########################################

echo ""
echo "✅ Playlisto started!"
echo ""
echo "🌐 Backend:  http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173"
echo ""
echo "📁 Logs folder: $LOG_DIR"
echo ""
echo "🛑 To stop run:"
echo "   ./stop.sh"
echo ""
