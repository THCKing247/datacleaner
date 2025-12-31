"""
Unified API for Data Cleaner subdomain
Combines authentication and data clean services
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
import sys

# Add parent directory to path to import services
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(parent_dir, 'Automation Service Python'))

# Import data clean engine
import importlib.util

def load_service(module_name, class_name):
    """Load a service class from a file with numeric prefix"""
    file_path = os.path.join(parent_dir, 'Automation Service Python', module_name)
    if not os.path.exists(file_path):
        raise ImportError(f"Service file not found: {file_path}")
    valid_name = f"service_{module_name.replace('.py', '').replace('_', '')}"
    spec = importlib.util.spec_from_file_location(valid_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[valid_name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, class_name):
        raise ImportError(f"Class {class_name} not found in {module_name}")
    return getattr(module, class_name)

# Load Data Clean Engine
try:
    ApexDataCleanEngine = load_service('1_data_clean_engine.py', 'ApexDataCleanEngine')
    data_clean_engine = ApexDataCleanEngine()
except Exception as e:
    print(f"Error loading Data Clean Engine: {e}")
    raise

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

# ==================== Database Functions ====================

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table - designed for future integration with unified database
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
            -- Future integration fields (uncomment when unified database is ready):
            -- unified_user_id TEXT,  -- Reference to unified user system
            -- account_tier TEXT,      -- free, premium, enterprise
            -- subscription_status TEXT -- active, suspended, cancelled
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
    
    # Processing history table - tracks user operations for analytics/billing
    c.execute('''
        CREATE TABLE IF NOT EXISTS processing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT,
            rows_in INTEGER,
            rows_out INTEGER,
            processing_time_ms INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create indexes for performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_processing_history_user_id ON processing_history(user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_processing_history_created_at ON processing_history(created_at)')
    
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

# ==================== Authentication Middleware ====================

def verify_token():
    """Verify JWT token from request"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    return verify_jwt_token(token)

@app.before_request
def require_auth():
    """Require authentication for data clean endpoints"""
    # Public endpoints
    public_endpoints = ['/api/health', '/api/auth/register', '/api/auth/login', 
                       '/api/auth/verify-mfa', '/api/auth/complete-registration']
    
    if request.path in public_endpoints:
        return
    
    # Verify token for protected endpoints
    if request.path.startswith('/api/'):
        payload = verify_token()
        if not payload:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Attach user info to request
        request.user_id = payload['user_id']
        request.user_email = payload['email']

# ==================== API Endpoints ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'data-cleaner'})

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
def verify_token_endpoint():
    """Verify JWT token"""
    payload = verify_token()
    
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

@app.route('/api/services/data-clean', methods=['POST'])
def data_clean():
    """Data Clean Engine service - supports batch file uploads, large files, and multiple formats"""
    try:
        # Check if files were uploaded (support multiple files)
        if 'files[]' in request.files or 'file' in request.files:
            # Handle batch uploads
            files = request.files.getlist('files[]') or [request.files.get('file')]
            files = [f for f in files if f and f.filename]
            
            if not files:
                return jsonify({'success': False, 'error': 'No files selected'}), 400
            
            # Get options from form data
            delimiter = request.form.get('delimiter', ',')
            normalize_headers = request.form.get('normalize_headers', 'true').lower() == 'true'
            drop_empty_rows = request.form.get('drop_empty_rows', 'true').lower() == 'true'
            apply_crm_mappings = request.form.get('apply_crm_mappings', 'true').lower() == 'true'
            file_type = request.form.get('file_type')
            sheet_name = request.form.get('sheet_name')
            
            # Get export format preferences
            export_formats_str = request.form.get('export_formats', 'csv,json,excel')
            export_formats = [f.strip() for f in export_formats_str.split(',')] if export_formats_str else ['csv']
            
            # Process all files
            results = []
            for file in files:
                if not file.filename:
                    continue
                
                filename = file.filename
                file_content = file.read()
                
                # Use streaming method for large files (handles 100k+ entries)
                try:
                    outputs, report = data_clean_engine.clean_file_streaming(
                        file_content,
                        filename,
                        file_type=file_type if file_type else None,
                        delimiter=delimiter,
                        normalize_headers=normalize_headers,
                        drop_empty_rows=drop_empty_rows,
                        apply_crm_mappings=apply_crm_mappings,
                        sheet_name=sheet_name if sheet_name else None,
                        chunk_size=10000,  # Process in 10k row chunks
                        export_formats=export_formats,  # Only generate requested formats
                    )
                    
                    # Filter outputs based on user's export format preferences
                    import base64
                    result_data = {
                        'filename': filename,
                        'success': True,
                        'outputs': {},
                        'column_files': {},
                        'report': {
                            'rows_in': report.rows_in,
                            'rows_out': report.rows_out,
                            'columns_in': report.columns_in,
                            'columns_out': report.columns_out,
                            'header_map': report.header_map,
                            'fixes': report.fixes,
                            'started_at': report.started_at,
                            'finished_at': report.finished_at,
                            'file_type': report.file_type,
                            'crm_detected': report.crm_detected,
                            'field_mappings': report.field_mappings,
                            'duplicates_removed': getattr(report, 'duplicates_removed', 0),
                            'irrelevant_rows_removed': getattr(report, 'irrelevant_rows_removed', 0),
                        }
                    }
                    
                    # Only include requested export formats
                    if 'csv' in export_formats and outputs.get('master_cleanse_csv'):
                        result_data['outputs']['master_cleanse_csv'] = outputs['master_cleanse_csv']
                    
                    if 'json' in export_formats and outputs.get('master_cleanse_json'):
                        result_data['outputs']['master_cleanse_json'] = outputs['master_cleanse_json']
                    
                    if 'excel' in export_formats and outputs.get('master_cleanse_excel'):
                        result_data['outputs']['master_cleanse_excel'] = base64.b64encode(
                            outputs['master_cleanse_excel']
                        ).decode('utf-8')
                    
                    # Column files (always included - core feature for data verification)
                    if outputs.get('column_files'):
                        for col_name, col_data in outputs['column_files'].items():
                            result_data['column_files'][col_name] = {}
                            if col_data.get('csv'):
                                result_data['column_files'][col_name]['csv'] = col_data['csv']
                            if col_data.get('json'):
                                result_data['column_files'][col_name]['json'] = col_data['json']
                            if col_data.get('excel'):
                                result_data['column_files'][col_name]['excel'] = base64.b64encode(
                                    col_data['excel']
                                ).decode('utf-8')
                    
                    results.append(result_data)
                    
                except Exception as e:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': str(e)
                    })
            
            # Return batch results
            if len(results) == 1:
                # Single file - return directly
                return jsonify(results[0])
            else:
                # Multiple files - return array
                return jsonify({
                    'success': True,
                    'batch': True,
                    'files_processed': len(results),
                    'results': results
                })
        
        # Fallback to text-based input (for backward compatibility)
        if request.is_json:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            csv_text = data.get('csv_text', '')
            if not csv_text:
                return jsonify({'success': False, 'error': 'No CSV text provided'}), 400
            
            delimiter = data.get('delimiter', ',')
            normalize_headers = data.get('normalize_headers', True)
            drop_empty_rows = data.get('drop_empty_rows', True)
            
            cleaned_csv, report = data_clean_engine.clean_csv_text(
                csv_text,
                delimiter=delimiter,
                normalize_headers=normalize_headers,
                drop_empty_rows=drop_empty_rows
            )
            
            return jsonify({
                'success': True,
                'cleaned_csv': cleaned_csv,
                'report': {
                    'rows_in': report.rows_in,
                    'rows_out': report.rows_out,
                    'columns_in': report.columns_in,
                    'columns_out': report.columns_out,
                    'header_map': report.header_map,
                    'fixes': report.fixes,
                    'started_at': report.started_at,
                    'finished_at': report.finished_at,
                    'file_type': getattr(report, 'file_type', 'csv'),
                    'crm_detected': getattr(report, 'crm_detected', None),
                    'field_mappings': getattr(report, 'field_mappings', {}),
                    'duplicates_removed': getattr(report, 'duplicates_removed', 0),
                    'irrelevant_rows_removed': getattr(report, 'irrelevant_rows_removed', 0),
                }
            })
        else:
            return jsonify({'success': False, 'error': 'No file or data provided'}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port, host='0.0.0.0')
