#!/bin/bash
# Install script for Claude for LibreOffice
# Handles dependencies and extension installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Claude for LibreOffice - Installer"
echo "========================================"
echo ""

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    elif [ -f /etc/debian_version ]; then
        OS="debian"
    elif [ -f /etc/fedora-release ]; then
        OS="fedora"
    elif [ -f /etc/arch-release ]; then
        OS="arch"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi
    echo $OS
}

OS=$(detect_os)
echo "Detected OS: $OS"
echo ""

# Check if Python scripting is available
check_python_uno() {
    python3 -c "import uno" 2>/dev/null
}

# Install dependencies based on OS
install_dependencies() {
    echo "Installing LibreOffice Python scripting support..."
    echo ""

    case $OS in
        ubuntu|debian|pop|linuxmint|elementary)
            sudo apt-get update
            sudo apt-get install -y libreoffice-script-provider-python python3-uno
            ;;
        fedora|rhel|centos)
            sudo dnf install -y libreoffice-pyuno
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -S --noconfirm python-uno
            ;;
        opensuse*)
            sudo zypper install -y libreoffice-pyuno
            ;;
        macos)
            echo "Python scripting is included in LibreOffice for macOS."
            echo "If not working, reinstall LibreOffice from https://www.libreoffice.org/download/"
            ;;
        *)
            echo "Unknown OS. Please install LibreOffice Python scripting manually:"
            echo "  - Look for a package named 'libreoffice-pyuno' or 'python3-uno'"
            return 1
            ;;
    esac
}

# Step 1: Check dependencies
echo "Step 1: Checking dependencies..."
echo ""

if ! command -v libreoffice &> /dev/null; then
    echo "[!] LibreOffice not found. Please install LibreOffice first."
    exit 1
fi
echo "[✓] LibreOffice installed"

if check_python_uno; then
    echo "[✓] Python scripting support available"
else
    echo "[!] Python scripting support NOT available"
    echo ""
    read -p "Install Python scripting support now? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        install_dependencies
        if check_python_uno; then
            echo "[✓] Python scripting support installed successfully"
        else
            echo "[!] Installation may have failed. Please install manually and retry."
            exit 1
        fi
    else
        echo "Skipping dependency installation. Extension may not work."
    fi
fi

echo ""

# Step 2: Build extension if needed
echo "Step 2: Building extension..."
echo ""

if [ ! -f "claude-for-libreoffice-1.0.0.oxt" ]; then
    if [ -f "build.sh" ]; then
        # Run build without interactive prompts
        ./build.sh <<< "y"
    else
        echo "[!] Extension file not found and build.sh missing"
        exit 1
    fi
else
    echo "[✓] Extension package found"
fi

echo ""

# Step 3: Close LibreOffice if running
echo "Step 3: Checking for running LibreOffice..."
if pgrep -f soffice > /dev/null; then
    echo "[!] LibreOffice is running. Please close it first."
    read -p "Close LibreOffice now? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        pkill -f soffice || true
        sleep 2
        echo "[✓] LibreOffice closed"
    fi
fi
echo ""

# Step 4: Remove old version if installed
echo "Step 4: Removing old version (if any)..."
if unopkg list 2>/dev/null | grep -q "com.anthropic.claude.libreoffice"; then
    unopkg remove com.anthropic.claude.libreoffice 2>/dev/null || true
    echo "[✓] Old version removed"
else
    echo "[✓] No previous version found"
fi
echo ""

# Step 5: Install extension
echo "Step 5: Installing extension..."
unopkg add claude-for-libreoffice-1.0.0.oxt
echo "[✓] Extension installed"
echo ""

# Step 6: Verify installation
echo "Step 6: Verifying installation..."
if unopkg list 2>/dev/null | grep -q "com.anthropic.claude.libreoffice"; then
    echo "[✓] Installation verified"
else
    echo "[!] Installation verification failed"
    exit 1
fi

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Open LibreOffice Calc"
echo "  2. Go to Tools menu → look for 'Claude:' items"
echo "  3. Click 'Claude: Configure API Key...' and enter your API key"
echo "  4. Select some cells and click 'Claude: Analyze Selection'"
echo ""
echo "Get your API key at: https://console.anthropic.com"
echo ""
