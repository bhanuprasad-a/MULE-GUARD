-- MuleGuard Core Banking Schema
-- Synthetic data only

CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(32) NOT NULL UNIQUE,
    device_fingerprint VARCHAR(128),
    ip_address INET,
    address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL
        REFERENCES customers(id),
    account_type VARCHAR(32) NOT NULL
        CHECK (account_type IN ('Current', 'Savings')),
    balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00
        CHECK (balance >= 0),
    status VARCHAR(32) NOT NULL DEFAULT 'Normal'
        CHECK (status IN (
            'Normal',
            'Under Review',
            'Flagged',
            'Critical',
            'Blocked'
        )),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(64) PRIMARY KEY,

    sender_account_id VARCHAR(32)
        REFERENCES accounts(id),

    receiver_account_id VARCHAR(32)
        REFERENCES accounts(id),

    amount NUMERIC(15, 2) NOT NULL
        CHECK (amount > 0),

    transaction_type VARCHAR(32) NOT NULL
        CHECK (transaction_type IN (
            'Transfer',
            'Payment',
            'Deposit',
            'Withdrawal'
        )),

    status VARCHAR(32) NOT NULL DEFAULT 'Completed'
        CHECK (status IN (
            'Pending',
            'Completed',
            'Failed',
            'Reversed'
        )),

    transaction_timestamp TIMESTAMPTZ NOT NULL,

    origin VARCHAR(255),
    destination VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        sender_account_id IS NOT NULL
        OR receiver_account_id IS NOT NULL
    ),

    CHECK (
        sender_account_id IS NULL
        OR receiver_account_id IS NULL
        OR sender_account_id <> receiver_account_id
    )
);

CREATE INDEX IF NOT EXISTS idx_accounts_customer
    ON accounts(customer_id);

CREATE INDEX IF NOT EXISTS idx_accounts_status
    ON accounts(status);

CREATE INDEX IF NOT EXISTS idx_transactions_sender
    ON transactions(sender_account_id);

CREATE INDEX IF NOT EXISTS idx_transactions_receiver
    ON transactions(receiver_account_id);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
    ON transactions(transaction_timestamp);

CREATE INDEX IF NOT EXISTS idx_transactions_sender_time
    ON transactions(sender_account_id, transaction_timestamp);

CREATE INDEX IF NOT EXISTS idx_transactions_receiver_time
    ON transactions(receiver_account_id, transaction_timestamp);