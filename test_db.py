import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    host=os.getenv("DATABASE_HOST", "127.0.0.1"),
    port=int(os.getenv("DATABASE_PORT", "5432")),
    dbname=os.getenv("DATABASE_NAME", "muleguard_bank"),
    user=os.getenv("DATABASE_USER", "postgres"),
    password=os.getenv("DATABASE_PASSWORD", ""),
)

print("✅ Connected to MuleGuard PostgreSQL!")

with conn.cursor() as cur:
    cur.execute("SELECT 1;")
    result = cur.fetchone()
    print("Database test:", result)

conn.close()