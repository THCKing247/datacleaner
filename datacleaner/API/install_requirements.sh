#!/bin/bash
# Install Data Cleaner API Dependencies
# This script handles Pillow installation issues on various platforms

echo "Installing Data Cleaner API Dependencies..."
echo ""

# Upgrade pip first
echo "Step 1: Upgrading pip..."
pip install --upgrade pip

# Try to install Pillow with pre-built wheel
echo ""
echo "Step 2: Installing Pillow (pre-built wheel)..."
pip install --only-binary :all: Pillow 2>/dev/null || pip install Pillow --no-cache-dir

# Install other dependencies
echo ""
echo "Step 3: Installing other dependencies..."
pip install Flask==3.0.0
pip install flask-cors==4.0.0
pip install Werkzeug==3.0.1
pip install PyJWT==2.8.0
pip install pyotp==2.9.0
pip install qrcode==7.4.2
pip install openpyxl==3.1.2

echo ""
echo "Installation complete!"

