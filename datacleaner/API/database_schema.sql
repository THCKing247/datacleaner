-- Data Cleaner Database Schema
-- This schema is designed to be extensible for future integration with unified website services

-- Users table - can be extended for unified user management
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
    locked_until TEXT,
    -- Future integration fields (can be added when unified database is implemented)
    -- unified_user_id TEXT,  -- Reference to unified user system
    -- account_tier TEXT,      -- free, premium, enterprise
    -- subscription_status TEXT -- active, suspended, cancelled
);

-- Sessions table - for session management
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Data processing history - tracks user's data cleaning operations
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
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_processing_history_user_id ON processing_history(user_id);
CREATE INDEX IF NOT EXISTS idx_processing_history_created_at ON processing_history(created_at);

-- Future tables for unified service integration:
-- 
-- service_subscriptions - Track which services users have access to
-- CREATE TABLE IF NOT EXISTS service_subscriptions (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     user_id INTEGER NOT NULL,
--     service_name TEXT NOT NULL,  -- 'data-cleaner', 'voice-of-customer', etc.
--     status TEXT NOT NULL,        -- 'active', 'suspended', 'cancelled'
--     started_at TEXT NOT NULL,
--     expires_at TEXT,
--     FOREIGN KEY (user_id) REFERENCES users (id)
-- );
--
-- usage_metrics - Track service usage for billing/analytics
-- CREATE TABLE IF NOT EXISTS usage_metrics (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     user_id INTEGER NOT NULL,
--     service_name TEXT NOT NULL,
--     metric_type TEXT NOT NULL,   -- 'file_processed', 'rows_cleaned', 'api_call'
--     metric_value INTEGER,
--     recorded_at TEXT NOT NULL,
--     FOREIGN KEY (user_id) REFERENCES users (id)
-- );

