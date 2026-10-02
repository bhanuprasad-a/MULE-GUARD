from app.db.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'rules'")
        print('Rules columns:', cur.fetchall())
        cur.execute("SELECT count(*) FROM rules")
        print('Count rules:', cur.fetchone()[0])
