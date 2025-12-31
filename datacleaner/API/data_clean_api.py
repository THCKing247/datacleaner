"""
Data Clean Engine API for Data Cleaner subdomain
Protected by authentication middleware
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import jwt

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

# Configuration (should match auth_api.py)
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

def verify_token():
    """Verify JWT token from request"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.before_request
def require_auth():
    """Require authentication for all endpoints except health check"""
    if request.path == '/api/health':
        return
    
    payload = verify_token()
    if not payload:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    # Attach user info to request
    request.user_id = payload['user_id']
    request.user_email = payload['email']

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'data-clean'})

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
    app.run(debug=True, port=5002)

