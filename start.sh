#!/bin/bash

echo "Starting Playlisto..."

cd backend

# activate venv if exists
if [ -d ".playlisto" ]; then
  source .playlisto/bin/activate
fi

uvicorn app.main:app --host 0.0.0.0 --port 8000
