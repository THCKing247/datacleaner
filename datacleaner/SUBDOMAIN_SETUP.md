# Data Cleaner Subdomain Setup

## Overview

This subdomain (`datacleaner.apextsgroup.com`) is a standalone service that provides:
1. **Login/Registration Page** - Entry point for all clients
2. **Data Cleaning Engine** - Accessible after authentication
3. **Database Integration Ready** - Prepared for future unified database integration

## User Flow

1. **Client visits subdomain** → Sees login page (`datacleaner/index.html`)
2. **Client logs in or registers** → Authentication via API
3. **After successful login** → Redirected to dashboard (`/dashboard/`)
4. **Dashboard loads** → Data Cleaning Engine interface is displayed
5. **Client can use engine** → Upload files, clean data, download results

## File Structure

```
datacleaner/
├── index.html              # Login/Registration page (ENTRY POINT)
├── dashboard/
│   └── index.html         # Protected dashboard with Data Clean Engine
├── API/
│   ├── app.py            # Unified API (auth + data cleaning)
│   ├── datacleaner.db    # SQLite database (auto-created)
│   └── requirements.txt  # Python dependencies
└── [shared assets from root]
    ├── assets/site.js    # Data Clean Engine UI
    └── assets/site.css   # Styling
```

## Authentication Flow

1. **Login Page** (`/` or `/index.html`)
   - Shows login form
   - Shows registration form (toggle)
   - Handles MFA setup during registration
   - Redirects to `/dashboard/` after successful login

2. **Dashboard** (`/dashboard/`)
   - Checks for authentication token
   - Redirects to login if no token
   - Loads Data Clean Engine interface
   - Displays user info and logout button

3. **API Endpoints** (`/api/`)
   - `/api/auth/login` - User login
   - `/api/auth/register` - User registration
   - `/api/auth/verify` - Token verification
   - `/api/services/data-clean` - Data cleaning (protected)

## Database Structure

The database is designed for future integration with a unified website database:

### Current Tables:
- **users** - User accounts with authentication
  - Includes fields for future integration (commented out)
  - `unified_user_id` - For linking to unified system
  - `account_tier` - For subscription management
  - `subscription_status` - For service access control

- **sessions** - Active user sessions
- **processing_history** - Tracks data cleaning operations

### Future Integration:
The schema includes commented fields that can be activated when integrating with the unified database system.

## Setup Instructions

### 1. Install Dependencies
```bash
cd datacleaner/API
pip install -r requirements.txt
```

### 2. Create First User
```bash
cd datacleaner/API
python quick_setup.py
```

Default credentials:
- Email: `admin@apextsgroup.com`
- Password: `Admin@123`

### 3. Start Server
```bash
cd datacleaner/API
python app.py
```

Server runs on `http://localhost:5001` (development) or configured port for production.

### 4. Access Application
- **Development**: `http://localhost:5001`
- **Production**: `https://datacleaner.apextsgroup.com`

## Web Server Configuration

For production deployment, configure your web server (nginx/Apache) to:

1. **Serve static files** from `datacleaner/` directory
2. **Proxy API requests** to `http://localhost:5001` (or configured port)
3. **Set up SSL** for HTTPS

### Nginx Example:
```nginx
server {
    listen 443 ssl;
    server_name datacleaner.apextsgroup.com;
    
    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Serve static files
    root /path/to/datacleaner;
    index index.html;
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Features

### Authentication
- ✅ JWT-based authentication
- ✅ Password hashing (Werkzeug)
- ✅ Multi-Factor Authentication (MFA/TOTP)
- ✅ Account locking after failed attempts
- ✅ Session management

### Data Cleaning Engine
- ✅ CSV, Excel, JSON file support
- ✅ Batch file processing
- ✅ Large file handling (100k+ rows)
- ✅ CRM field mapping (Salesforce, HubSpot, etc.)
- ✅ Column-based exports
- ✅ Multiple export formats (CSV, JSON, Excel)
- ✅ Original filename preserved with "(Cleaned)" suffix

### Database Integration Ready
- ✅ Schema designed for unified database
- ✅ User table includes integration fields
- ✅ Processing history tracking
- ✅ Extensible for service subscriptions

## Security

- Passwords are hashed using Werkzeug
- JWT tokens expire after 24 hours
- CORS configured for subdomain
- Account locking after 5 failed login attempts
- MFA support for additional security

## Future Integration

When integrating with the unified website database:

1. **Uncomment integration fields** in database schema
2. **Update user creation** to link with unified user system
3. **Add service subscription checks** before allowing data cleaning
4. **Sync user data** between systems
5. **Implement usage tracking** for billing/analytics

See `database_integration.md` for detailed integration guide.

