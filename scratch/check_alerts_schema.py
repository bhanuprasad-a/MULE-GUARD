from app.db.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT severity, count(*) FROM alerts GROUP BY severity")
        print('Severity counts:', cur.fetchall())
        cur.execute("SELECT status, count(*) FROM alerts GROUP BY status")
        print('Alert status counts:', cur.fetchall())
        cur.execute("SELECT id, name FROM rules")
        print('Rules in DB:', cur.fetchall())
