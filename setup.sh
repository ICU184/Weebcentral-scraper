#!/bin/bash

# Setup script for WeebCentral Scraper on macOS
# This script installs Python 3 and required dependencies

set -e  # Exit on any error

echo "===== WeebCentral Scraper Setup ====="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "✓ Homebrew is already installed"
fi

# Install Python 3
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "Installing Python 3..."
    brew install python3
else
    echo "✓ Python 3 is already installed"
    python3 --version
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install required Python packages
echo ""
echo "Installing required Python packages..."
python3 -m pip install requests Pillow

echo ""
echo "===== Setup Complete! ====="
echo ""
echo "You can now run the scraper with:"
echo "  python3 weebcentral_scraper.py"
echo ""
