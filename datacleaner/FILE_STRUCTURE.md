# Data Cleaner - Complete File Structure

This document lists all files in the Data Cleaner subdomain project.

## Directory Structure

```
datacleaner/
├── index.html                    # Login/Registration page
├── dashboard/
│   └── index.html               # Protected dashboard with Data Clean Engine
├── API/
│   ├── app.py                   # Main unified API (auth + data cleaning)
│   ├── requirements.txt         # Python dependencies
│   ├── quick_setup.py           # Quick admin user creation script
│   ├── create_admin_user.py     # Interactive admin user creation
│   ├── install_requirements.bat # Windows installation script
│   ├── install_requirements.sh  # Linux/Mac installation script
│   ├── database_schema.sql      # Database schema with integration points
│   └── datacleaner.db           # SQLite database (created on first run)
├── README.md                     # Main setup and configuration guide
├── ACCESS.md                     # Access credentials and login guide
├── QUICK_START.md                # Quick start reference
├── INSTALL_TROUBLESHOOTING.md    # Installation troubleshooting (in API/)
└── FILE_STRUCTURE.md             # This file
```

## Key Files Description

### Frontend Files
- **index.html** - Login/registration page with MFA setup
- **dashboard/index.html** - Main dashboard with Data Clean Engine interface

### Backend Files
- **API/app.py** - Unified Flask API with authentication and data cleaning endpoints
- **API/requirements.txt** - All Python package dependencies
- **API/database_schema.sql** - SQL schema ready for unified database integration

### Setup Scripts
- **API/quick_setup.py** - Creates default admin user (admin@apextsgroup.com / Admin@123)
- **API/create_admin_user.py** - Interactive script for creating custom admin users
- **API/install_requirements.bat** - Windows dependency installer
- **API/install_requirements.sh** - Linux/Mac dependency installer

### Documentation
- **README.md** - Complete setup guide, API endpoints, security features
- **ACCESS.md** - Login credentials, password requirements, troubleshooting
- **QUICK_START.md** - Quick reference for getting started
- **API/database_integration.md** - Guide for integrating with unified database
- **API/INSTALL_TROUBLESHOOTING.md** - Solutions for installation issues

## Dependencies

The Data Cleaner requires:
- Python 3.8+
- Flask and related packages (see requirements.txt)
- Access to the parent directory's `Automation Service Python/1_data_clean_engine.py`

## Database

- SQLite database created automatically at: `API/datacleaner.db`
- Schema includes users, sessions, and processing_history tables
- Designed for future integration with unified database system

## Default Credentials

After running `quick_setup.py`:
- Email: admin@apextsgroup.com
- Password: Admin@123
- **Change password after first login!**

