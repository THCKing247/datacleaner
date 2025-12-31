"""
Authentication API for Data Cleaner subdomain
Implements industry-standard authentication with MFA support
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets
import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
import re
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
DB_PATH = os.path.join(os.path.dirname(__file__), 'datacleaner.db')

# Password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS = {
    'uppercase': r'[A-Z]',
    'lowercase': r'[a-z]',
    'digit': r'\d',
    'special': r'[@$!%*?&]'
}

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            mfa_secret TEXT,
            mfa_enabled INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            last_login TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def validate_password(password):
    """Validate password meets requirements"""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    
    for req_name, pattern in PASSWORD_REQUIREMENTS.items():
        if not re.search(pattern, password):
            return False, f"Password must contain at least one {req_name} character"
    
    return True, None

def generate_jwt_token(user_id, email):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_by_email(email):
    """Get user from database by email"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'email': user[1],
            'name': user[2],
            'password_hash': user[3],
            'mfa_secret': user[4],
            'mfa_enabled': bool(user[5]),
            'created_at': user[6],
            'last_login': user[7],
            'failed_login_attempts': user[8],
            'locked_until': user[9]
        }
    return None

def update_user(user_id, **kwargs):
    """Update user fields"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    updates = []
    values = []
    for key, value in kwargs.items():
        updates.append(f"{key} = ?")
        values.append(value)
    
    values.append(user_id)
    c.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()

def create_user(email, name, password_hash, mfa_secret=None):
    """Create a new user"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO users (email, name, password_hash, mfa_secret, mfa_enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, name, password_hash, mfa_secret, 1 if mfa_secret else 0, datetime.utcnow().isoformat()))
        
        user_id = c.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def generate_mfa_qr(secret, email):
    """Generate QR code for MFA setup"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name='Data Cleaner'
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.read()).decode()
    return f"data:image/png;base64,{img_base64}"

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not email or not name or not password:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Check if user exists
        if get_user_by_email(email):
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Generate MFA secret
        mfa_secret = pyotp.random_base32()
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user (temporarily, will be completed after MFA verification)
        user_id = create_user(email, name, password_hash, mfa_secret)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Registration failed'}), 400
        
        # Generate QR code
        qr_url = generate_mfa_qr(mfa_secret, email)
        
        return jsonify({
            'success': True,
            'mfa_secret': mfa_secret,
            'mfa_qr_url': qr_url,
            'message': 'Please set up MFA to complete registration'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/complete-registration', methods=['POST'])
def complete_registration():
    """Complete registration after MFA setup"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        password = data.get('password', '')
        mfa_secret = data.get('mfa_secret')
        
        if not email or not name or not password:
            return jsonify({'success': False, 'error': 'Missing registration data'}), 400
        
        user = get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found. Please register first.'}), 404
        
        # If MFA secret provided, verify it was set up correctly
        if mfa_secret:
            # User has MFA, registration is complete
            update_user(user['id'], mfa_enabled=1)
        else:
            # User skipped MFA, can enable later
            update_user(user['id'], mfa_secret=None, mfa_enabled=0)
        
        # Generate token
        token = generate_jwt_token(user['id'], user['email'])
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'mfa_enabled': bool(mfa_secret)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user with optional MFA"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        mfa_code = data.get('mfa_code')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        user = get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Check if account is locked
        if user['locked_until']:
            lock_time = datetime.fromisoformat(user['locked_until'])
            if datetime.utcnow() < lock_time:
                return jsonify({
                    'success': False,
                    'error': f'Account locked. Try again after {lock_time.strftime("%Y-%m-%d %H:%M:%S")} UTC'
                }), 423
        
        # Verify password
        if not check_password_hash(user['password_hash'], password):
            # Increment failed attempts
            failed_attempts = user['failed_login_attempts'] + 1
            if failed_attempts >= 5:
                # Lock account for 30 minutes
                lock_until = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
                update_user(user['id'], failed_login_attempts=failed_attempts, locked_until=lock_until)
                return jsonify({
                    'success': False,
                    'error': 'Too many failed attempts. Account locked for 30 minutes.'
                }), 423
            else:
                update_user(user['id'], failed_login_attempts=failed_attempts)
            
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Check MFA
        if user['mfa_enabled'] and user['mfa_secret']:
            if not mfa_code:
                # Return that MFA is required
                return jsonify({
                    'success': False,
                    'requires_mfa': True,
                    'error': 'MFA code required'
                }), 200
            
            # Verify MFA code
            totp = pyotp.TOTP(user['mfa_secret'])
            if not totp.verify(mfa_code, valid_window=1):
                return jsonify({'success': False, 'error': 'Invalid MFA code'}), 401
        
        # Reset failed attempts and update last login
        update_user(
            user['id'],
            failed_login_attempts=0,
            locked_until=None,
            last_login=datetime.utcnow().isoformat()
        )
        
        # Generate token
        token = generate_jwt_token(user['id'], user['email'])
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'mfa_enabled': user['mfa_enabled']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Verify JWT token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'No token provided'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
    
    user = get_user_by_email(payload['email'])
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'mfa_enabled': user['mfa_enabled']
        }
    })

@app.route('/api/auth/verify-mfa', methods=['POST'])
def verify_mfa():
    """Verify MFA code during setup"""
    try:
        data = request.get_json()
        mfa_secret = data.get('mfa_secret')
        mfa_code = data.get('mfa_code')
        
        if not mfa_secret or not mfa_code:
            return jsonify({'success': False, 'error': 'MFA secret and code are required'}), 400
        
        totp = pyotp.TOTP(mfa_secret)
        if totp.verify(mfa_code, valid_window=1):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid MFA code'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'auth'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)

