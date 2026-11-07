#!/bin/bash
set -e

# ==============================================================================
# Playlisto - Automated Unified Installer
# Supports: Arch Linux, Ubuntu / Debian, PRoot Linux, and Termux
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
# 2. Operating System & Privilege Detection
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

# Sudo helper (handles root in PRoot/Termux vs standard user)
if [ "$EUID" -eq 0 ]; then
    SUDO=""
elif command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
elif command -v doas >/dev/null 2>&1; then
    SUDO="doas"
else
    SUDO=""
fi

# ==============================================================================
# 3. System Dependencies Check & Fix (with runtime tests)
# ==============================================================================
echo -e "\n${CYAN}📦 Checking system dependencies...${NC}"

# Helper function to test if npm is actually functional (not broken by glob/esm errors)
is_npm_working() {
    if ! command -v npm >/dev/null 2>&1; then
        return 1
    fi
    # Execute npm --version and check exit code without dumping node stacktrace
    if npm --version >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Helper function to test if python venv module is usable
is_venv_working() {
    if ! command -v python3 >/dev/null 2>&1; then
        return 1
    fi
    if python3 -c "import venv, ensurepip" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to fix/install broken or missing npm
fix_or_install_npm() {
    echo -e "\n${YELLOW}⚠️  Node.js or npm is missing or broken (e.g. missing glob / CJS module error).${NC}"
    read -rp "Would you like to install/fix Node.js and npm automatically? [Y/n]: " fix_npm_choice
    case "$fix_npm_choice" in
        [nN][oO]|[nN])
            echo -e "${YELLOW}Skipping npm fix. Note: Frontend build may fail if npm is non-functional.${NC}"
            return 1
            ;;
        *)
            echo -e "${CYAN}Attempting to repair Node.js and npm...${NC}"
            if [ "$OS_TYPE" == "ubuntu" ]; then
                # First try reinstalling via apt
                $SUDO apt update -y || true
                $SUDO apt install --reinstall -y nodejs npm || true

                # If still broken, install clean NodeSource Node.js LTS
                if ! is_npm_working; then
                    echo -e "${YELLOW}Apt npm package is incompatible with installed Node. Installing NodeSource Node.js LTS...${NC}"
                    if command -v curl >/dev/null 2>&1; then
                        curl -fsSL https://deb.nodesource.com/setup_20.x | $SUDO bash -
                        $SUDO apt install -y nodejs
                    elif command -v wget >/dev/null 2>&1; then
                        wget -qO- https://deb.nodesource.com/setup_20.x | $SUDO bash -
                        $SUDO apt install -y nodejs
                    fi
                fi
            elif [ "$OS_TYPE" == "arch" ]; then
                $SUDO pacman -Sy --needed --noconfirm nodejs npm
            elif [ "$OS_TYPE" == "termux" ]; then
                pkg install -y nodejs
            fi

            if is_npm_working; then
                echo -e "${GREEN}✓ npm is now working successfully ($(npm --version))!${NC}"
                return 0
            else
                echo -e "${RED}❌ Could not automatically repair npm. Please check your Node/npm installation.${NC}"
                return 1
            fi
            ;;
    esac
}

# Function to install missing python3-venv
install_python_venv() {
    echo -e "\n${YELLOW}⚠️  Python virtual environment module (python3-venv / ensurepip) is not installed.${NC}"
    read -rp "Would you like to install python3-venv now? [Y/n]: " install_venv_choice
    case "$install_venv_choice" in
        [nN][oO]|[nN])
            echo -e "${RED}❌ Python virtual environment support is required. Exiting.${NC}"
            exit 1
            ;;
        *)
            echo -e "${CYAN}Installing Python virtual environment packages...${NC}"
            if [ "$OS_TYPE" == "ubuntu" ]; then
                $SUDO apt update -y || true
                $SUDO apt install -y python3-venv python3-pip
            elif [ "$OS_TYPE" == "arch" ]; then
                $SUDO pacman -Sy --needed --noconfirm python python-pip
            elif [ "$OS_TYPE" == "termux" ]; then
                pkg install -y python
            else
                echo -e "${RED}❌ Please install python3-venv manually for your system.${NC}"
                exit 1
            fi
            ;;
    esac
}

# 3.1 Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${YELLOW}Python 3 is not installed.${NC}"
    read -rp "Would you like to install Python 3 now? [Y/n]: " install_py_choice
    case "$install_py_choice" in
        [nN][oO]|[nN])
            echo -e "${RED}❌ Python 3 is required. Exiting.${NC}"
            exit 1
            ;;
        *)
            if [ "$OS_TYPE" == "ubuntu" ]; then
                $SUDO apt update -y && $SUDO apt install -y python3 python3-pip python3-venv
            elif [ "$OS_TYPE" == "arch" ]; then
                $SUDO pacman -Sy --needed --noconfirm python python-pip
            elif [ "$OS_TYPE" == "termux" ]; then
                pkg install -y python
            fi
            ;;
    esac
fi

# 3.2 Check venv capability
if ! is_venv_working; then
    install_python_venv
fi

# 3.3 Check Node & NPM
if ! is_npm_working; then
    fix_or_install_npm || true
fi

# 3.4 Check Git
if ! command -v git >/dev/null 2>&1; then
    echo -e "${YELLOW}Git is not installed.${NC}"
    read -rp "Would you like to install git now? [Y/n]: " install_git_choice
    case "$install_git_choice" in
        [nN][oO]|[nN]) ;;
        *)
            if [ "$OS_TYPE" == "ubuntu" ]; then
                $SUDO apt install -y git
            elif [ "$OS_TYPE" == "arch" ]; then
                $SUDO pacman -Sy --needed --noconfirm git
            elif [ "$OS_TYPE" == "termux" ]; then
                pkg install -y git
            fi
            ;;
    esac
fi

# Display summary of detected tools
echo -e "   ${GREEN}✓ Python:${NC} $(python3 -V 2>&1)"
if command -v node >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Node.js:${NC} $(node -v 2>&1)"
fi
if is_npm_working; then
    echo -e "   ${GREEN}✓ npm:${NC} v$(npm --version 2>&1)"
fi

# ==============================================================================
# 4. Setup Python Backend Environment
# ==============================================================================
echo -e "\n${CYAN}🐍 Setting up Python backend environment...${NC}"
cd "$ROOT_DIR/backend"

VENV_DIR="$ROOT_DIR/backend/.playlisto"

if [ -d "$VENV_DIR" ]; then
    echo -e "   ${YELLOW}📁 Existing virtual environment found at:${NC} backend/.playlisto"
    read -rp "   Do you want to remove it and create a fresh one? [y/N]: " overwrite_venv
    case "$overwrite_venv" in
        [yY][eE][sS]|[yY])
            echo -e "   ${CYAN}🗑️  Removing existing virtual environment...${NC}"
            rm -rf "$VENV_DIR"
            echo "   Creating new Python virtual environment in backend/.playlisto..."
            python3 -m venv "$VENV_DIR"
            ;;
        *)
            echo "   Keeping and using existing virtual environment."
            ;;
    esac
else
    echo "   Creating Python virtual environment in backend/.playlisto..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Check if packages are already installed or need install
if python -c "import fastapi, uvicorn, httpx, cryptography, mutagen" >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Required Python packages are already installed.${NC}"
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

if is_npm_working; then
    if [ -d "node_modules" ] && [ -f "node_modules/.bin/vite" ]; then
        echo -e "   ${GREEN}✓ Node modules are already installed.${NC}"
    else
        echo "   Installing Node dependencies (npm install)..."
        npm install --quiet
    fi

    echo "   Building frontend for production (npm run build)..."
    npm run build --quiet
    echo -e "   ${GREEN}✓ Frontend built into frontend/dist${NC}"
else
    echo -e "${YELLOW}⚠️  npm is currently not functional. Skipping frontend build step.${NC}"
    echo "You can build the frontend later with 'npm install && npm run build' once npm is repaired."
fi

# ==============================================================================
# 6. Ensure Permissions on Control Scripts
# ==============================================================================
chmod +x "$ROOT_DIR/start.sh" "$ROOT_DIR/stop.sh" "$ROOT_DIR/install.sh" 2>/dev/null || true

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
