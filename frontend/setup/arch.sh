#!/bin/bash

echo "🔄 Updating Arch..."
pacman -Syu

echo "📦 Installing Node.js (includes npm)..."
pacman -Sy nodejs npm

echo "✅ Node version: $(node -v)"
echo "✅ NPM version: $(npm -v)"

# If package.json exists, install dependencies
if [ -f package.json ]; then
    echo "📦 Installing npm dependencies..."
    npm install
else
    echo "⚠ No package.json found in this directory."
    echo "✅ COPY this setup to frontend directory and run."
    echo "✅ Use command : cp $0 ../"
fi

echo ""
echo "🚀 Done!"
