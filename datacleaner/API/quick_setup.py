"""
Quick setup script to create admin user and start server
Usage: python quick_setup.py [email] [name] [password]
"""

import sys
import os
from werkzeug.security import generate_password_hash
import pyotp
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import init_db, create_user, get_user_by_email, update_user, generate_mfa_qr

def create_default_admin():
    """Create a default admin user"""
    print("=" * 60)
    print("Data Cleaner - Quick Admin Setup")
    print("=" * 60)
    print()
    
    # Default credentials (user can change these)
    email = "admin@apextsgroup.com"
    name = "Admin User"
    password = "Admin@123"  # Change this after first login!
    
    # Check if user already exists
    init_db()
    existing_user = get_user_by_email(email)
    
    if existing_user:
        print(f"[OK] User {email} already exists!")
        print(f"   You can log in with:")
        print(f"   Email: {email}")
        print(f"   Password: [your existing password]")
        return True
    
    # Hash password
    password_hash = generate_password_hash(password)
    
    # Create user without MFA for quick setup (can enable later)
    user_id = create_user(email, name, password_hash, mfa_secret=None)
    
    if user_id:
        print(f"[OK] Admin user created successfully!")
        print()
        print("=" * 60)
        print("Login Credentials")
        print("=" * 60)
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print()
        print("[!] IMPORTANT: Change this password after first login!")
        print()
        print("You can now:")
        print("1. Log in at: http://localhost:5001")
        print("2. Enable MFA from your account settings (recommended)")
        print("3. Change your password")
        print()
        return True
    else:
        print("[ERROR] Error creating user")
        return False

if __name__ == '__main__':
    try:
        create_default_admin()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

