from app.db.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'accounts'")
        print('Columns in accounts:', cur.fetchall())
        cur.execute("SELECT status, count(*) FROM accounts GROUP BY status")
        print('Status counts in accounts:', cur.fetchall())
        cur.execute("SELECT count(*) FROM accounts")
        print('Total accounts in DB:', cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM transactions")
        print('Total transactions in DB:', cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM alerts")
        print('Total alerts in DB:', cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM cases")
        print('Total cases in DB:', cur.fetchone()[0])
