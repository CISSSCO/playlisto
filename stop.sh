#!/bin/bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/playlisto.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "❌ No running Playlisto instance found."
  exit 1
fi

read BACKEND_PID FRONTEND_PID < "$PID_FILE"

echo "🛑 Stopping Backend (PID: $BACKEND_PID)..."
kill "$BACKEND_PID" 2>/dev/null || kill -9 "$BACKEND_PID" 2>/dev/null

echo "🛑 Stopping Frontend (PID: $FRONTEND_PID)..."
kill "$FRONTEND_PID" 2>/dev/null || kill -9 "$FRONTEND_PID" 2>/dev/null

# Clean up any leftover uvicorn or vite processes if any
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

rm -f "$PID_FILE"

echo "✅ Playlisto stopped successfully."
