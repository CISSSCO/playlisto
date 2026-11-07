#!/bin/bash
set -e

# ==============================================================================
# Playlisto - Automated Unified Installer
# Supports: Arch Linux, Ubuntu / Debian, and derivatives
# ==============================================================================

# Terminal Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "=========================================================="
echo "           🎵 Welcome to the Playlisto Installer          "
echo "=========================================================="
echo -e "${NC}"

# ==============================================================================
# 1. Locate Playlisto Project Root
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/backend/app/main.py" ] && [ -f "$SCRIPT_DIR/frontend/package.json" ]; then
    ROOT_DIR="$SCRIPT_DIR"
elif [ -d "$HOME/git/playlisto" ] && [ -f "$HOME/git/playlisto/backend/app/main.py" ]; then
    ROOT_DIR="$HOME/git/playlisto"
elif [ -d "$PWD/backend" ] && [ -d "$PWD/frontend" ]; then
    ROOT_DIR="$PWD"
else
    echo -e "${RED}❌ Could not locate the Playlisto repository.${NC}"
    echo "Please run this installer from inside the Playlisto directory or copy it into the repository root."
    exit 1
fi

echo -e "${BLUE}📁 Project directory:${NC} $ROOT_DIR"

# ==============================================================================
# 2. Operating System Detection
# ==============================================================================
echo -e "\n${CYAN}🔍 Detecting Operating System...${NC}"

OS_TYPE="unknown"
DISTRO_NAME="Unknown Linux"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_NAME="${PRETTY_NAME:-$NAME}"

    if [[ "$ID" == "arch" || "$ID_LIKE" =~ "arch" || -x "$(command -v pacman)" ]]; then
        OS_TYPE="arch"
    elif [[ "$ID" == "ubuntu" || "$ID" == "debian" || "$ID_LIKE" =~ "debian" || -x "$(command -v apt)" ]]; then
        OS_TYPE="ubuntu"
    fi
elif [ -n "$PREFIX" ] && [ -d "/data/data/com.termux" ]; then
    OS_TYPE="termux"
    DISTRO_NAME="Termux (Android)"
fi

echo -e "   Detected: ${BOLD}$DISTRO_NAME${NC} (Type: ${GREEN}$OS_TYPE${NC})"

if [ "$OS_TYPE" == "unknown" ]; then
    echo -e "${YELLOW}⚠️  Warning: OS not explicitly recognized as Arch or Ubuntu/Debian.${NC}"
    echo "Attempting to continue using installed system binaries..."
fi

# ==============================================================================
# 3. System Dependencies Check / Install
# ==============================================================================
echo -e "\n${CYAN}📦 Checking system dependencies...${NC}"

MISSING_PKGS=()

command -v python3 >/dev/null 2>&1 || MISSING_PKGS+=("python3")
command -v node >/dev/null 2>&1 || MISSING_PKGS+=("nodejs")
command -v npm >/dev/null 2>&1 || MISSING_PKGS+=("npm")
command -v git >/dev/null 2>&1 || MISSING_PKGS+=("git")

if [ ${#MISSING_PKGS[@]} -eq 0 ]; then
    echo -e "   ${GREEN}✓ All core binaries found:${NC} python3 ($(python3 -V 2>&1)), node ($(node -v 2>&1)), npm ($(npm -v 2>&1)), git"
else
    echo -e "   ${YELLOW}Missing tools: ${MISSING_PKGS[*]}${NC}"
    echo -e "   Installing missing packages..."

    if [ "$OS_TYPE" == "arch" ]; then
        if [ "$EUID" -ne 0 ]; then
            sudo pacman -Sy --needed --noconfirm python python-pip nodejs npm git make gcc openssl libffi pkg-config
        else
            pacman -Sy --needed --noconfirm python python-pip nodejs npm git make gcc openssl libffi pkg-config
        fi
    elif [ "$OS_TYPE" == "ubuntu" ]; then
        if [ "$EUID" -ne 0 ]; then
            sudo apt update -y
            sudo apt install -y python3 python3-pip python3-venv nodejs npm git make gcc libssl-dev libffi-dev pkg-config
        else
            apt update -y
            apt install -y python3 python3-pip python3-venv nodejs npm git make gcc libssl-dev libffi-dev pkg-config
        fi
    elif [ "$OS_TYPE" == "termux" ]; then
        pkg update -y
        pkg install -y python nodejs git make clang openssl libffi
    else
        echo -e "${RED}❌ Please install the missing packages manually: ${MISSING_PKGS[*]}${NC}"
        exit 1
    fi
fi

# ==============================================================================
# 4. Setup Python Backend Environment
# ==============================================================================
echo -e "\n${CYAN}🐍 Setting up Python backend environment...${NC}"
cd "$ROOT_DIR/backend"

VENV_DIR="$ROOT_DIR/backend/.playlisto"

if [ ! -d "$VENV_DIR" ]; then
    echo "   Creating Python virtual environment in backend/.playlisto..."
    python3 -m venv "$VENV_DIR"
else
    echo "   Existing virtual environment detected in backend/.playlisto."
fi

# Activate venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if python -c "import fastapi, uvicorn, httpx, cryptography, mutagen" >/dev/null 2>&1; then
    echo "   ✓ Required Python packages are already installed."
else
    echo "   Installing backend requirements from requirements.txt..."
    pip install --upgrade pip setuptools wheel --quiet 2>/dev/null || true
    pip install -r requirements.txt --quiet
fi

# Ensure data directory exists
mkdir -p "$ROOT_DIR/backend/data"
chmod 700 "$ROOT_DIR/backend/data" 2>/dev/null || true

# Verify backend import
echo "   Verifying backend installation..."
python -c "import app.main; print('   ✓ Backend modules verified successfully.')"

# ==============================================================================
# 5. Setup Frontend Web Player
# ==============================================================================
echo -e "\n${CYAN}⚛️  Setting up React frontend...${NC}"
cd "$ROOT_DIR/frontend"

if [ -d "node_modules" ] && [ -f "node_modules/.bin/vite" ]; then
    echo "   ✓ Node modules are already installed."
else
    echo "   Installing Node dependencies (npm install)..."
    npm install --quiet
fi

echo "   Building frontend for production (npm run build)..."
npm run build --quiet
echo "   ✓ Frontend built into frontend/dist"

# ==============================================================================
# 6. Ensure Permissions on Control Scripts
# ==============================================================================
chmod +x "$ROOT_DIR/start.sh" "$ROOT_DIR/stop.sh" 2>/dev/null || true

# ==============================================================================
# 7. Installation Complete & Instructions
# ==============================================================================
echo -e "\n${GREEN}${BOLD}==========================================================${NC}"
echo -e "${GREEN}${BOLD}           🎉 Playlisto Setup Complete!                  ${NC}"
echo -e "${GREEN}${BOLD}==========================================================${NC}"

echo -e "\n${BOLD}🚀 How to Launch & Run:${NC}"
echo -e "   1. Start all services in background:"
echo -e "      ${CYAN}${BOLD}./start.sh${NC}"
echo -e ""
echo -e "   2. Stop all running services:"
echo -e "      ${CYAN}${BOLD}./stop.sh${NC}"
echo -e ""
echo -e "${BOLD}🌐 Access Points:${NC}"
echo -e "   • ${BOLD}Web Player:${NC}   ${CYAN}http://localhost:5173${NC} (Dev server)"
echo -e "   • ${BOLD}Production:${NC}   ${CYAN}http://localhost:8000${NC} (Served via FastAPI)"
echo -e "   • ${BOLD}API Docs:${NC}     ${CYAN}http://localhost:8000/docs${NC} (Interactive Swagger UI)"
echo -e ""
echo -e "${BOLD}⚙️  Initial Setup in the Web Player:${NC}"
echo -e "   1. Open ${CYAN}http://localhost:5173${NC} in your browser."
echo -e "   2. Click the ${BOLD}☰${NC} hamburger menu at top-right to open ${BOLD}Settings${NC}."
echo -e "   3. In ${BOLD}Providers${NC}: Enter a name (e.g., 'My Drive') and your ${BOLD}Google Drive API Key${NC}."
echo -e "   4. In ${BOLD}Sources${NC}: Enter a source name, paste your ${BOLD}Google Drive Folder URL${NC}, select the provider, and click ${BOLD}Add Source${NC}."
echo -e "   5. Close settings and click ${BOLD}Load Active Source${NC} to start playing!"
echo -e ""
echo -e "${GREEN}Enjoy your music with Playlisto! 🎧${NC}\n"
