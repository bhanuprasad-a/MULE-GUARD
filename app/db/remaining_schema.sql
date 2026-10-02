CREATE TABLE IF NOT EXISTS watchlists (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES accounts(id),
    reason TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'Active'
        CHECK (status IN ('Active', 'Removed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS decisions (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES accounts(id),
    alert_id VARCHAR(64) REFERENCES alerts(id),
    decision VARCHAR(32) NOT NULL
        CHECK (decision IN ('Monitor', 'Clear', 'Block', 'Escalate')),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rules (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS networks (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    risk_score NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_watchlists_account
ON watchlists(account_id);

CREATE INDEX IF NOT EXISTS idx_decisions_account
ON decisions(account_id);

CREATE INDEX IF NOT EXISTS idx_rules_enabled
ON rules(enabled);