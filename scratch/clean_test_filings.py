import sys
sys.path.insert(0, '.')
from app.db.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM regulatory_filings WHERE reason LIKE '%Automated%';")
        conn.commit()
        cur.execute("SELECT id, filing_type, status, reason FROM regulatory_filings ORDER BY id;")
        rows = cur.fetchall()
        print(f"Current regulatory filings count: {len(rows)}")
        for r in rows:
            print(" ", r)
