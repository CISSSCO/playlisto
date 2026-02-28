#!/bin/bash

PID_FILE="playlisto.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "❌ No running Playlisto instance found."
  exit 1
fi

read BACKEND_PID FRONTEND_PID < "$PID_FILE"

echo "🛑 Stopping Backend (PID: $BACKEND_PID)..."
kill -9 -$BACKEND_PID 2>/dev/null

echo "🛑 Stopping Frontend (PID: $FRONTEND_PID)..."
kill -9 -$FRONTEND_PID 2>/dev/null

rm -f "$PID_FILE"

echo "✅ Playlisto stopped successfully."
