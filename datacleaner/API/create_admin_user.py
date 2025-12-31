"""
Script to create an admin user for Data Cleaner
Run this script to set up your first admin account
"""

import sys
import os
import getpass
from werkzeug.security import generate_password_hash
import pyotp
import qrcode
import io
import base64
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import init_db, create_user, get_user_by_email, update_user, generate_mfa_qr

def create_admin():
    """Create an admin user interactively"""
    print("=" * 60)
    print("Data Cleaner - Admin User Setup")
    print("=" * 60)
    print()
    
    # Get user details
    name = input("Enter full name: ").strip()
    if not name:
        print("Error: Name is required")
        return
    
    email = input("Enter email address: ").strip().lower()
    if not email:
        print("Error: Email is required")
        return
    
    # Check if user already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        print(f"User with email {email} already exists!")
        overwrite = input("Do you want to reset password? (y/n): ").strip().lower()
        if overwrite != 'y':
            return
        user_id = existing_user['id']
    else:
        user_id = None
    
    # Get password
    password = getpass.getpass("Enter password: ")
    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        return
    
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        return
    
    # Ask about MFA
    enable_mfa = input("Enable MFA? (y/n): ").strip().lower() == 'y'
    
    # Initialize database
    init_db()
    
    # Hash password
    password_hash = generate_password_hash(password)
    
    # Generate MFA secret if enabled
    mfa_secret = None
    if enable_mfa:
        mfa_secret = pyotp.random_base32()
    
    # Create or update user
    if user_id:
        # Update existing user
        update_user(
            user_id,
            name=name,
            password_hash=password_hash,
            mfa_secret=mfa_secret,
            mfa_enabled=1 if mfa_secret else 0
        )
        print(f"\n✅ User {email} updated successfully!")
    else:
        # Create new user
        user_id = create_user(email, name, password_hash, mfa_secret)
        if user_id:
            print(f"\n✅ User {email} created successfully!")
        else:
            print(f"\n❌ Error creating user")
            return
    
    # Display MFA setup if enabled
    if enable_mfa and mfa_secret:
        print("\n" + "=" * 60)
        print("MFA Setup Required")
        print("=" * 60)
        print(f"\nSecret: {mfa_secret}")
        print("\nScan this QR code with your authenticator app:")
        print("(Google Authenticator, Authy, Microsoft Authenticator, etc.)")
        print()
        
        qr_url = generate_mfa_qr(mfa_secret, email)
        print(f"QR Code URL: {qr_url[:50]}...")
        print("\nOr enter this code manually in your authenticator app:")
        print(f"Secret: {mfa_secret}")
        print()
        print("After scanning, you can log in at: http://localhost:5001")
        print("Use your email and password, then enter the 6-digit code from your app.")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print(f"\nYou can now log in with:")
    print(f"  Email: {email}")
    print(f"  Password: [the password you entered]")
    if enable_mfa:
        print(f"  MFA: Required (use authenticator app)")
    print(f"\nAccess the site at: http://localhost:5001")
    print()

if __name__ == '__main__':
    try:
        create_admin()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

