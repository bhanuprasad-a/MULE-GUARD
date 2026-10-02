"""
MuleGuard Auth Audit Log Viewer
Prints the most recent authentication and biometric audit events from PostgreSQL.
"""

import sys
from app.db.database import get_connection
from psycopg.rows import dict_row

limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10

with get_connection() as conn:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT event_timestamp, event_type, employee_id, ip_address, outcome, failure_reason, details
            FROM auth_audit_log
            ORDER BY event_timestamp DESC
            LIMIT %s;
            """,
            (limit,)
        )
        rows = cur.fetchall()

print(f"\n--- Recent Authentication & Biometric Audit Events (Last {len(rows)}) ---")
for r in rows:
    ts = r['event_timestamp'].strftime("%H:%M:%S")
    print(f"[{ts}] {r['event_type']:<24} | User: {str(r['employee_id']):<11} | Outcome: {r['outcome']:<7} | Reason: {str(r['failure_reason']):<28} | Details: {r['details']}")
