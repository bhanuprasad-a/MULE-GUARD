from app.db.database import get_connection


with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, status
            FROM accounts
            WHERE status IN (
                'Flagged',
                'Critical',
                'Blocked',
                'Under Review'
            )
            ORDER BY id
            LIMIT 5
            """
        )

        for row in cur.fetchall():
            print(row)