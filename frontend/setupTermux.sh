#!/data/data/com.termux/files/usr/bin/bash

echo "🔄 Updating Termux..."
pkg update -y && pkg upgrade -y

echo "📦 Installing Node.js (includes npm)..."
pkg install -y nodejs

echo "✅ Node version: $(node -v)"
echo "✅ NPM version: $(npm -v)"

# If package.json exists, install dependencies
if [ -f package.json ]; then
    echo "📦 Installing npm dependencies..."
    npm install
else
    echo "⚠ No package.json found in this directory."
fi

echo ""
echo "🚀 Done!"
