-- MuleGuard Institutional Authentication Schema
-- Isolated from banking customer/account/transaction data

CREATE TABLE IF NOT EXISTS auth_roles (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auth_permissions (
    id VARCHAR(64) PRIMARY KEY,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_role_permissions (
    role_id VARCHAR(32) NOT NULL REFERENCES auth_roles(id) ON DELETE CASCADE,
    permission_id VARCHAR(64) NOT NULL REFERENCES auth_permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS auth_users (
    id VARCHAR(36) PRIMARY KEY,
    employee_id VARCHAR(32) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    department VARCHAR(64) NOT NULL,
    title VARCHAR(64) NOT NULL,
    role_id VARCHAR(32) NOT NULL REFERENCES auth_roles(id),
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('PENDING_ENROLLMENT', 'ACTIVE', 'SUSPENDED', 'LOCKED', 'DEACTIVATED')),
    must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    last_password_change_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_users_employee_id ON auth_users(employee_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_status ON auth_users(status);

CREATE TABLE IF NOT EXISTS auth_biometric_credentials (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    algorithm VARCHAR(64) NOT NULL DEFAULT 'facenet-512',
    embedding_dimension INT NOT NULL DEFAULT 512,
    encrypted_embedding BYTEA NOT NULL,
    encryption_key_id VARCHAR(64) NOT NULL DEFAULT 'k1',
    encryption_nonce BYTEA NOT NULL,
    encryption_tag BYTEA NOT NULL,
    template_version INT NOT NULL DEFAULT 1,
    enrollment_quality_score NUMERIC(5, 2) NOT NULL DEFAULT 98.50,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'REVOKED', 'SUPERSEDED')),
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_auth_biometric_user ON auth_biometric_credentials(user_id);

CREATE TABLE IF NOT EXISTS auth_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_token_hash VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(36) NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    role_id VARCHAR(32) NOT NULL REFERENCES auth_roles(id),
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    device_fingerprint_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revocation_reason VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash ON auth_sessions(session_token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_active ON auth_sessions(user_id, is_revoked, expires_at);

CREATE TABLE IF NOT EXISTS auth_audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(64) NOT NULL,
    user_id VARCHAR(36) REFERENCES auth_users(id) ON DELETE SET NULL,
    employee_id VARCHAR(32),
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    outcome VARCHAR(16) NOT NULL CHECK (outcome IN ('SUCCESS', 'FAILURE', 'BLOCKED')),
    failure_reason VARCHAR(128),
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_auth_audit_timestamp ON auth_audit_log(event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_auth_audit_event_type ON auth_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_audit_user_id ON auth_audit_log(user_id);
