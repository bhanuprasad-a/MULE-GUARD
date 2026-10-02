from app.db.database import get_connection
from app.services.risk_engine import analyze_account

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, status FROM accounts WHERE status != 'Normal' ORDER BY status, id")
        rows = cur.fetchall()
        print(f"Non-normal accounts in DB ({len(rows)}):")
        for r in rows:
            res = analyze_account(r[0])
            print(f"{r[0]} ({r[1]}): score={res['risk_score']} prob={res['risk_probability']:.4f}")

        cur.execute("SELECT id FROM accounts WHERE status = 'Normal' LIMIT 5")
        for r in cur.fetchall():
            res = analyze_account(r[0])
            print(f"Normal {r[0]}: score={res['risk_score']} prob={res['risk_probability']:.4f}")
