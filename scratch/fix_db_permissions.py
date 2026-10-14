import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def fix_permissions():
    admin_user = os.getenv("DB_ADMIN_USER", "postgres")
    admin_pass = os.getenv("DB_ADMIN_PASSWORD")
    app_user = os.getenv("DATABASE_USER", "muleguard_app")
    dbname = os.getenv("DATABASE_NAME", "muleguard_bank")
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")

    print(f"Connecting to {dbname} as admin {admin_user}...")
    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=admin_user,
        password=admin_pass,
        autocommit=True
    )
    cur = conn.cursor()

    cur.execute(f"GRANT ALL ON SCHEMA public TO {app_user};")
    cur.execute(f"ALTER DATABASE {dbname} OWNER TO {app_user};")

    # Transfer ownership of all tables and views and sequences
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    tables = cur.fetchall()
    for (t,) in tables:
        cur.execute(f'ALTER TABLE "{t}" OWNER TO {app_user};')
        print(f"Set owner of table {t} to {app_user}")

    cur.execute("SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public';")
    seqs = cur.fetchall()
    for (s,) in seqs:
        cur.execute(f'ALTER SEQUENCE "{s}" OWNER TO {app_user};')
        print(f"Set owner of sequence {s} to {app_user}")

    print("Permissions and ownership successfully granted to", app_user)
    conn.close()

if __name__ == "__main__":
    fix_permissions()
