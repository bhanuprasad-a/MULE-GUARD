"""
MuleGuard Regulatory Filings Database Table & Initial Seed Migration
Creates the regulatory_filings table in PostgreSQL and seeds initial realistic filings.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.database import get_connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS regulatory_filings (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES accounts(id),
    case_id VARCHAR(64) REFERENCES cases(id),
    alert_id VARCHAR(64) REFERENCES alerts(id),
    filing_type VARCHAR(32) NOT NULL CHECK (filing_type IN ('SAR', 'STR', 'CTR', 'NTR')),
    status VARCHAR(32) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Accepted', 'Rejected')),
    reporting_authority VARCHAR(64) NOT NULL DEFAULT 'FIU-IND',
    reason TEXT,
    narrative TEXT,
    reference_number VARCHAR(128),
    filed_by VARCHAR(64) DEFAULT 'A. Kumar',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regulatory_filings_account ON regulatory_filings(account_id);
CREATE INDEX IF NOT EXISTS idx_regulatory_filings_status ON regulatory_filings(status);
CREATE INDEX IF NOT EXISTS idx_regulatory_filings_created ON regulatory_filings(created_at DESC);
"""

INITIAL_FILINGS = [
    (
        "FIL-IND-2026-001",
        "ACC-982054",
        "CS-982054",
        "ALT-982054",
        "SAR",
        "Accepted",
        "FIU-IND",
        "Fan-In Collection Syndicate mule pattern with rapid velocity and cross-bank dissipation.",
        "Account exhibited rapid multi-source inbound aggregation followed by swift outbound dispersion to 5 high-risk counterparties within a 45-minute window. Confirmed mule pattern matching typology MULE-FANIN-COLLECTION.",
        "FIU-ACK-982054-01",
        "A. Kumar",
        "2026-08-10 14:30:00+05:30",
        "2026-08-12 11:15:00+05:30"
    ),
    (
        "FIL-IND-2026-002",
        "ACC-982060",
        "CS-982060",
        "ALT-982060",
        "STR",
        "Submitted",
        "FIU-IND",
        "Fan-Out Smurfing Ring structured pass-through transactions exceeding statutory AML monitoring thresholds.",
        "High-velocity structuring observed with multiple sub-threshold withdrawals immediately post high-volume credit. ML mule score 0.88 with graph degree anomaly.",
        "FIU-ACK-982060-02",
        "A. Kumar",
        "2026-08-15 16:45:00+05:30",
        "2026-08-16 10:00:00+05:30"
    ),
    (
        "FIL-IND-2026-003",
        "ACC-982066",
        "CS-982066",
        "ALT-982066",
        "SAR",
        "Draft",
        "FIU-IND",
        "Dormant Account Activation Ring: Account dormant >90 days receiving immediate high-value inbound transfers.",
        "Account created >90 days prior with zero transaction history suddenly received multiple UPI and IMPS transactions totaling >₹250,000 within 24 hours. Rule R-DORM-1 triggered.",
        None,
        "A. Kumar",
        "2026-09-01 09:20:00+05:30",
        "2026-09-01 09:20:00+05:30"
    ),
    (
        "FIL-IND-2026-004",
        "ACC-982070",
        "CS-982070",
        "ALT-982070",
        "CTR",
        "Draft",
        "FIU-IND",
        "Shared Infrastructure Syndicate: Device fingerprint and IP address linked to 3+ suspicious mule accounts.",
        "Network Intelligence identified identical device fingerprint and IP cluster shared across Raghav Choudhury, Ashok Kulkarni, and Sandesh Patel. Coordinated cash flow and mule syndicate operations.",
        None,
        "A. Kumar",
        "2026-09-18 11:05:00+05:30",
        "2026-09-18 11:05:00+05:30"
    )
]

def init_table_and_seed():
    print("[MuleGuard] Initializing regulatory_filings table...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            
            # Check existing count
            cur.execute("SELECT COUNT(*) FROM regulatory_filings;")
            count = cur.fetchone()[0]
            if count == 0:
                print("[MuleGuard] Seeding initial regulatory filings...")
                for item in INITIAL_FILINGS:
                    cur.execute(
                        """
                        INSERT INTO regulatory_filings (
                            id, account_id, case_id, alert_id, filing_type, status,
                            reporting_authority, reason, narrative, reference_number,
                            filed_by, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING;
                        """,
                        item
                    )
                conn.commit()
                print(f"[MuleGuard] Seeded {len(INITIAL_FILINGS)} regulatory filings successfully.")
            else:
                print(f"[MuleGuard] regulatory_filings already contains {count} records.")

if __name__ == "__main__":
    init_table_and_seed()
