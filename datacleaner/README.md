# Data Cleaner Subdomain

A dedicated subdomain for the Data Clean Engine service with industry-standard authentication and MFA support.

## Features

- **Secure Authentication**: JWT-based authentication with password hashing
- **Multi-Factor Authentication (MFA)**: TOTP-based MFA using authenticator apps
- **Password Security**: Strong password requirements (uppercase, lowercase, number, special character)
- **Account Protection**: Failed login attempt tracking and account locking
- **Data Clean Engine**: Full-featured data cleaning service with all existing functionality

## Setup

### 1. Install Dependencies

```bash
cd datacleaner/API
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in `datacleaner/API/`:

```env
SECRET_KEY=your-secret-key-here-change-in-production
PORT=5001
```

**Important**: Generate a strong secret key for production:
```python
import secrets
print(secrets.token_hex(32))
```

### 3. Start the API Server

```bash
cd datacleaner/API
python auth_api.py
```

The API will run on `http://localhost:5001` by default.

### 4. Configure Web Server

For the subdomain `datacleaner.apextsgroup.com`, configure your web server (nginx, Apache, etc.) to:

1. Serve static files from the `datacleaner/` directory
2. Proxy API requests to `http://localhost:5001`

#### Nginx Example Configuration

```nginx
server {
    listen 80;
    server_name datacleaner.apextsgroup.com;

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

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/complete-registration` - Complete registration after MFA setup
- `POST /api/auth/login` - Login with email/password (and optional MFA code)
- `GET /api/auth/verify` - Verify JWT token
- `POST /api/auth/verify-mfa` - Verify MFA code during setup

### Data Clean Engine

- `POST /api/services/data-clean` - Clean data files (requires authentication)

## Security Features

1. **Password Hashing**: Uses Werkzeug's secure password hashing
2. **JWT Tokens**: Secure token-based authentication
3. **MFA Support**: TOTP-based two-factor authentication
4. **Account Locking**: Automatic account locking after 5 failed login attempts
5. **Password Requirements**: Enforces strong password policies
6. **SQL Injection Protection**: Uses parameterized queries
7. **CORS**: Configured for secure cross-origin requests

## Database

The application uses SQLite by default (stored in `datacleaner/API/datacleaner.db`). For production, consider upgrading to PostgreSQL or MySQL.

### Database Schema

- **users**: Stores user accounts, passwords (hashed), and MFA secrets
- **sessions**: Stores active sessions (optional, for session management)

## Production Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Enable HTTPS/SSL
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Review and harden security headers
- [ ] Test MFA setup and login flows
- [ ] Configure email service for password resets (future enhancement)

## Development

To run in development mode:

```bash
cd datacleaner/API
python auth_api.py
```

The API will run with debug mode enabled on port 5001.

## Notes

- The Data Clean Engine functionality remains unchanged from the main application
- All existing features (batch processing, large files, multiple formats, column-based exports) are preserved
- Authentication is required for all data cleaning operations
- Users can skip MFA during registration but are encouraged to enable it

