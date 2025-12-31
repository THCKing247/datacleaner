# Data Cleaner - Quick Start Guide

## Access Credentials

**There are NO default credentials.** You must create your first user account.

## Step 1: Create Your First User

### Method 1: Admin Script (Easiest)

```bash
cd datacleaner/API
python create_admin_user.py
```

Follow the prompts to create your account.

### Method 2: Web Registration

1. Start the server:
   ```bash
   cd datacleaner/API
   python app.py
   ```

2. Open browser: `http://localhost:5001`

3. Click "Register" and fill in the form

## Step 2: Log In

1. Go to: `http://localhost:5001`
2. Enter your email and password
3. If MFA is enabled, enter the 6-digit code from your authenticator app

## Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter  
- At least one number
- At least one special character (@$!%*?&)

Example: `MyP@ssw0rd123`

## Database Integration Ready

The system is designed to integrate with a unified database:

- ✅ Flexible schema with integration points
- ✅ Processing history tracking
- ✅ User management extensible for unified system
- ✅ See `database_integration.md` for full details

## Files Created

- `database_schema.sql` - Complete database schema
- `database_integration.md` - Integration guide
- `create_admin_user.py` - Admin user setup script
- `ACCESS.md` - Complete access documentation

## Next Steps

1. Create your admin user (see above)
2. Log in and test the Data Clean Engine
3. Review `database_integration.md` for future unified database setup

