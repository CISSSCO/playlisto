#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 Updating Termux..."
apt update -y && apt upgrade -y

echo "📦 Installing required system packages..."
apt install -y python3 rust clang make openssl libffi pkg-config

# Uncomment below 3 lines if running on android
#echo "🔧 Setting Android API level..."
#export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)
#echo "ANDROID_API_LEVEL=$ANDROID_API_LEVEL"

# Make it permanent if not already
if ! grep -q ANDROID_API_LEVEL ~/.bashrc; then
    echo "export ANDROID_API_LEVEL=$ANDROID_API_LEVEL" >> ~/.bashrc
fi

echo "🧹 Removing old virtual environment (if exists)..."
rm -rf .playlisto

echo "🐍 Creating new virtual environment..."
python3 -m venv .playlisto

echo "⚡ Activating virtual environment..."
source .playlisto/bin/activate

echo "⬆ Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel

echo "🔐 Installing cryptography first..."
pip install cryptography

echo "📚 Installing project requirements..."
pip install -r requirements.txt

echo ""
echo "✅ Setup Complete!"
echo "👉 To activate later run:"
echo "   source .playlisto/bin/activate"
