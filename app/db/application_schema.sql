CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL
        REFERENCES accounts(id),
    risk_score NUMERIC(5, 2) NOT NULL
        CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_probability NUMERIC(8, 6) NOT NULL
        CHECK (risk_probability >= 0 AND risk_probability <= 1),
    prediction INTEGER NOT NULL
        CHECK (prediction IN (0, 1)),
    severity VARCHAR(32) NOT NULL
        CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    status VARCHAR(32) NOT NULL DEFAULT 'Open'
        CHECK (status IN ('Open', 'Acknowledged', 'Resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_account
    ON alerts(account_id);

CREATE INDEX IF NOT EXISTS idx_alerts_status
    ON alerts(status);

CREATE INDEX IF NOT EXISTS idx_alerts_created
    ON alerts(created_at DESC);


CREATE TABLE IF NOT EXISTS cases (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL
        REFERENCES accounts(id),
    alert_id VARCHAR(64)
        REFERENCES alerts(id),
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'Open'
        CHECK (status IN (
            'Open',
            'Investigating',
            'Escalated',
            'Resolved'
        )),
    priority VARCHAR(32) NOT NULL DEFAULT 'Medium'
        CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_account
    ON cases(account_id);

CREATE INDEX IF NOT EXISTS idx_cases_status
    ON cases(status);


CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(128) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64),
    account_id VARCHAR(32)
        REFERENCES accounts(id),
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_account
    ON audit_logs(account_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created
    ON audit_logs(created_at DESC);