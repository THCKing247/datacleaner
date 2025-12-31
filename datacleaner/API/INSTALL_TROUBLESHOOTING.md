# Installation Troubleshooting Guide

## Pillow Build Error

If you're getting "Failed to build 'Pillow' when getting requirements to build wheel", try these solutions:

### Solution 1: Use Pre-built Wheel (Recommended for Windows)

```bash
pip install --upgrade pip
pip install --only-binary :all: Pillow
pip install -r requirements.txt
```

### Solution 2: Install Pillow Separately First

```bash
pip install --upgrade pip
pip install Pillow --no-cache-dir
pip install -r requirements.txt
```

### Solution 3: Use the Installation Script

**Windows:**
```bash
install_requirements.bat
```

**Linux/Mac:**
```bash
chmod +x install_requirements.sh
./install_requirements.sh
```

### Solution 4: Install System Dependencies (Linux)

If on Linux, you may need system libraries:

```bash
# Ubuntu/Debian
sudo apt-get install python3-dev python3-pil libjpeg-dev zlib1g-dev

# CentOS/RHEL
sudo yum install python3-devel python3-pillow libjpeg-devel zlib-devel

# Then install Python packages
pip install -r requirements.txt
```

### Solution 5: Use Conda (Alternative)

If pip continues to fail, use conda:

```bash
conda install pillow
pip install -r requirements.txt
```

### Solution 6: Skip QR Code Feature (Temporary)

If you don't need MFA QR codes immediately, you can temporarily remove Pillow:

1. Edit `requirements.txt` and remove the `Pillow` line
2. Edit `app.py` and comment out QR code generation (MFA will still work with manual secret entry)

## Other Common Issues

### "Module not found" Errors

Make sure you're in the correct directory and using the right Python:

```bash
cd datacleaner/API
python --version  # Should be Python 3.8+
pip install -r requirements.txt
```

### Permission Errors

On Linux/Mac, you might need sudo (not recommended) or use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### SSL Certificate Errors

If you get SSL errors:

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## Verification

After installation, verify everything works:

```bash
python -c "import flask, pyotp, qrcode, PIL; print('All imports successful!')"
```

If this command runs without errors, installation was successful!

