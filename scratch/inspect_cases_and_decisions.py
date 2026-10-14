import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, account_id, alert_id, title, status, priority, created_at FROM cases;")
        cases = cur.fetchall()
        print(f"Total cases ({len(cases)}):")
        for c in cases:
            print(" ", c)
        
        cur.execute("SELECT id, account_id, alert_id, decision, reason, created_at FROM decisions;")
        decisions = cur.fetchall()
        print(f"\nTotal decisions ({len(decisions)}):")
        for d in decisions:
            print(" ", d)
