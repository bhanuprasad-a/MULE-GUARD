import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import get_connection

def inspect_details():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY';
            """)
            print("Foreign keys:")
            for r in cur.fetchall():
                print(f"  {r[0]}.{r[1]} -> {r[2]}.{r[3]}")

            print("\nSample customer:")
            cur.execute("SELECT * FROM customers LIMIT 1;")
            print(" ", cur.fetchone())

            print("\nSample account:")
            cur.execute("SELECT * FROM accounts LIMIT 1;")
            print(" ", cur.fetchone())

            print("\nSample transaction:")
            cur.execute("SELECT * FROM transactions LIMIT 1;")
            print(" ", cur.fetchone())

if __name__ == "__main__":
    inspect_details()
