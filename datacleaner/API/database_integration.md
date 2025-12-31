# Database Integration Guide

This document outlines how to integrate the Data Cleaner database with a unified website service database system.

## Current Database Structure

The Data Cleaner uses SQLite by default, but the schema is designed to be easily migrated to PostgreSQL, MySQL, or integrated into a unified database system.

### Core Tables

1. **users** - User accounts with authentication
2. **sessions** - Active user sessions
3. **processing_history** - Tracks data cleaning operations

## Integration Strategies

### Option 1: Separate Database with Foreign Key References

Keep Data Cleaner database separate but add references to unified system:

```sql
-- Add unified user reference
ALTER TABLE users ADD COLUMN unified_user_id TEXT;

-- Add service subscription tracking
CREATE TABLE service_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unified_user_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    expires_at TEXT
);
```

### Option 2: Migrate to Unified Database

Move all tables to the unified database and update connection strings:

```python
# In app.py, change DB_PATH to point to unified database
DB_PATH = os.environ.get('UNIFIED_DB_PATH', 'unified_database.db')
```

### Option 3: Database Abstraction Layer

Create a database service layer that can work with either:

```python
# database_service.py
class DatabaseService:
    def __init__(self, db_type='sqlite', connection_string=None):
        if db_type == 'unified':
            # Connect to unified database
            self.conn = connect_to_unified_db(connection_string)
        else:
            # Use local SQLite
            self.conn = sqlite3.connect(DB_PATH)
    
    def get_user(self, email):
        # Query from unified or local database
        pass
```

## Recommended Integration Points

### 1. User Management

When unified user system is ready:

```python
# In app.py, modify get_user_by_email to check unified system first
def get_user_by_email(email):
    # Try unified database first
    unified_user = unified_db.get_user(email)
    if unified_user:
        # Sync with local database or use unified user directly
        return sync_user_data(unified_user)
    
    # Fallback to local database
    return get_local_user(email)
```

### 2. Service Access Control

Add service-level access control:

```python
def check_service_access(user_id, service_name='data-cleaner'):
    """Check if user has access to data cleaner service"""
    # Query unified service_subscriptions table
    subscription = unified_db.get_subscription(user_id, service_name)
    return subscription and subscription['status'] == 'active'
```

### 3. Usage Tracking

Track usage for billing/analytics:

```python
def record_usage(user_id, service_name, metric_type, value):
    """Record service usage"""
    unified_db.insert_usage_metric(
        user_id=user_id,
        service_name=service_name,
        metric_type=metric_type,
        metric_value=value,
        recorded_at=datetime.utcnow().isoformat()
    )
```

## Migration Script

When ready to migrate, use this script structure:

```python
# migrate_to_unified.py
import sqlite3
from unified_database import UnifiedDB

def migrate_users():
    """Migrate users from local to unified database"""
    local_conn = sqlite3.connect('datacleaner.db')
    unified_db = UnifiedDB()
    
    local_users = local_conn.execute('SELECT * FROM users').fetchall()
    
    for user in local_users:
        unified_db.create_user(
            email=user[1],
            name=user[2],
            password_hash=user[3],
            # ... other fields
        )
    
    print(f"Migrated {len(local_users)} users")

def migrate_history():
    """Migrate processing history"""
    # Similar migration logic
    pass
```

## Environment Variables for Integration

Add these to your `.env` file when ready:

```env
# Database Configuration
DB_TYPE=unified  # 'sqlite' or 'unified'
UNIFIED_DB_HOST=your-db-host
UNIFIED_DB_PORT=5432
UNIFIED_DB_NAME=apex_services
UNIFIED_DB_USER=db_user
UNIFIED_DB_PASSWORD=db_password

# Service Configuration
SERVICE_NAME=data-cleaner
REQUIRE_SUBSCRIPTION=true
```

## API Endpoints for Integration

The current API is designed to be extended:

```python
# Future endpoints for unified system
@app.route('/api/admin/users', methods=['GET'])
def list_users():
    """List all users (admin only)"""
    # Query unified database
    pass

@app.route('/api/admin/usage', methods=['GET'])
def get_usage_stats():
    """Get usage statistics"""
    # Query unified metrics
    pass
```

## Testing Integration

Create a test script to verify integration:

```python
# test_integration.py
def test_unified_user_lookup():
    """Test that users can be found in unified system"""
    user = unified_db.get_user('test@example.com')
    assert user is not None
    assert user['email'] == 'test@example.com'

def test_service_access():
    """Test service access control"""
    has_access = check_service_access(user_id=1, service_name='data-cleaner')
    assert has_access == True
```

## Notes

- The current SQLite database can coexist with a unified database
- All user operations can be gradually migrated
- Processing history can be synced or kept separate
- Authentication tokens can be shared across services if using unified auth

