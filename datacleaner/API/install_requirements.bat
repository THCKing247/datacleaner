@echo off
echo Installing Data Cleaner API Dependencies...
echo.

REM Try installing Pillow first with pre-built wheel
echo Step 1: Installing Pillow (pre-built wheel)...
pip install --upgrade pip
pip install --only-binary :all: Pillow

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Pillow installation failed. Trying alternative method...
    pip install Pillow --no-cache-dir
)

echo.
echo Step 2: Installing other dependencies...
pip install Flask==3.0.0
pip install flask-cors==4.0.0
pip install Werkzeug==3.0.1
pip install PyJWT==2.8.0
pip install pyotp==2.9.0
pip install qrcode==7.4.2
pip install openpyxl==3.1.2

echo.
echo Installation complete!
echo.
pause

