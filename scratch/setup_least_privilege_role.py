"""
MuleGuard Least-Privilege Database Role Provisioner
Creates role `muleguard_app` (NOSUPERUSER, NOCREATEDB, NOCREATEROLE)
Grants SELECT, INSERT, UPDATE, DELETE on all application tables and sequences.
"""

import os
import secrets
import string
import psycopg
from dotenv import load_dotenv

load_dotenv()

admin_user = os.getenv("DB_ADMIN_USER", "postgres")
admin_password = os.getenv("DB_ADMIN_PASSWORD", os.getenv("DATABASE_PASSWORD", ""))
host = os.getenv("DATABASE_HOST", "localhost")
port = int(os.getenv("DATABASE_PORT", "5432"))
dbname = os.getenv("DATABASE_NAME", "muleguard_bank")

# Generate secure password for muleguard_app
charset = string.ascii_letters + string.digits + "_-!@"
app_password = "".join(secrets.choice(charset) for _ in range(24))

conn = psycopg.connect(
    host=host,
    port=port,
    dbname=dbname,
    user=admin_user,
    password=admin_password,
    autocommit=True
)

with conn.cursor() as cur:
    # 1. Check if role exists
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'muleguard_app';")
    exists = cur.fetchone()
    if exists:
        cur.execute(f"ALTER ROLE muleguard_app WITH PASSWORD '{app_password}' NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN;")
        print("Role muleguard_app updated with fresh credentials and least-privilege attributes.")
    else:
        cur.execute(f"CREATE ROLE muleguard_app WITH LOGIN PASSWORD '{app_password}' NOSUPERUSER NOCREATEDB NOCREATEROLE;")
        print("Role muleguard_app created with least-privilege attributes.")

    # 2. Grant permissions on database and schema
    cur.execute("GRANT CONNECT ON DATABASE muleguard_bank TO muleguard_app;")
    cur.execute("GRANT USAGE ON SCHEMA public TO muleguard_app;")
    cur.execute("REVOKE CREATE ON SCHEMA public FROM muleguard_app;")

    # 3. Grant table permissions
    cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO muleguard_app;")
    cur.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO muleguard_app;")

    # 4. Default privileges for any future tables created by admin
    cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO muleguard_app;")
    cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO muleguard_app;")

conn.close()

# Update .env securely without printing password to console
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
with open(env_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
user_updated = False
pwd_updated = False
admin_user_present = False
admin_pwd_present = False

for line in lines:
    if line.startswith("DATABASE_USER="):
        new_lines.append("DATABASE_USER=muleguard_app\n")
        user_updated = True
    elif line.startswith("DATABASE_PASSWORD="):
        new_lines.append(f"DATABASE_PASSWORD={app_password}\n")
        pwd_updated = True
    elif line.startswith("DB_ADMIN_USER="):
        admin_user_present = True
        new_lines.append(line)
    elif line.startswith("DB_ADMIN_PASSWORD="):
        admin_pwd_present = True
        new_lines.append(line)
    else:
        new_lines.append(line)

if not admin_user_present:
    new_lines.append(f"DB_ADMIN_USER={admin_user}\n")
if not admin_pwd_present:
    new_lines.append(f"DB_ADMIN_PASSWORD={admin_password}\n")

with open(env_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✅ Role muleguard_app successfully provisioned and .env updated without logging credentials.")
