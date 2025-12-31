# Data Cleaner Access Guide

## Initial Setup

The Data Cleaner subdomain requires user registration. There are **no default credentials** - you must create your first user account.

## Creating Your First User

### Option 1: Use the Admin Setup Script (Recommended)

1. Navigate to the API directory:
   ```bash
   cd datacleaner/API
   ```

2. Run the admin user creation script:
   ```bash
   python create_admin_user.py
   ```

3. Follow the prompts:
   - Enter your full name
   - Enter your email address
   - Enter a password (must be at least 8 characters with uppercase, lowercase, number, and special character)
   - Choose whether to enable MFA (recommended)

4. If you enable MFA:
   - Scan the QR code with an authenticator app (Google Authenticator, Authy, etc.)
   - Save the secret code in a secure location
   - You'll need to enter a 6-digit code from your app when logging in

### Option 2: Register Through the Web Interface

1. Start the API server:
   ```bash
   cd datacleaner/API
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5001
   ```
   (Or your configured subdomain: `https://datacleaner.apextsgroup.com`)

3. Click "Register" on the login page

4. Fill in the registration form:
   - Full Name
   - Email Address
   - Password (must meet requirements)
   - Confirm Password

5. Set up MFA (optional but recommended):
   - Scan the QR code with your authenticator app
   - Enter the 6-digit code to verify
   - Or click "Skip for Now" to enable later

## Logging In

1. Go to the login page: `http://localhost:5001` (or your subdomain)

2. Enter your credentials:
   - **Email**: The email you registered with
   - **Password**: Your password

3. If MFA is enabled:
   - After entering email/password, you'll be prompted for an MFA code
   - Open your authenticator app
   - Enter the 6-digit code

4. You'll be redirected to the dashboard where you can use the Data Clean Engine

## Password Requirements

Your password must:
- Be at least 8 characters long
- Contain at least one uppercase letter (A-Z)
- Contain at least one lowercase letter (a-z)
- Contain at least one number (0-9)
- Contain at least one special character (@$!%*?&)

Example valid passwords:
- `MyP@ssw0rd`
- `Secure123!`
- `Data$Clean2024`

## MFA Setup

Multi-Factor Authentication (MFA) adds an extra layer of security:

1. **During Registration**: You'll see a QR code to scan
2. **Authenticator Apps**: Use any TOTP-compatible app:
   - Google Authenticator
   - Authy
   - Microsoft Authenticator
   - 1Password
   - LastPass Authenticator

3. **Manual Entry**: If you can't scan the QR code, enter the secret code manually in your app

4. **Verification**: Enter the 6-digit code from your app to complete setup

## Account Security Features

- **Account Locking**: After 5 failed login attempts, your account is locked for 30 minutes
- **Password Hashing**: Passwords are securely hashed using industry-standard methods
- **JWT Tokens**: Secure token-based authentication
- **Session Management**: Tokens expire after 24 hours

## Troubleshooting

### "Account locked" Error
- Wait 30 minutes after 5 failed login attempts
- Or contact support to unlock your account

### "Invalid MFA code" Error
- Make sure your device's time is synchronized
- Wait for a new code (codes refresh every 30 seconds)
- Verify you're using the correct authenticator app

### "User not found" Error
- Make sure you've registered first
- Check that you're using the correct email address
- Try registering again if needed

### Can't Access the Site
- Make sure the API server is running: `python app.py`
- Check that the server is running on port 5001
- Verify your web server configuration if using a subdomain

## Database Integration

The system is designed to integrate with a unified database system. See `database_integration.md` for details on:
- Current database structure
- Integration strategies
- Migration paths
- Service access control

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the README.md for setup instructions
3. Check database_integration.md for database-related questions

