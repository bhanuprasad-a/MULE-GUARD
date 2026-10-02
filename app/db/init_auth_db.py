"""
MuleGuard Authentication Database Initializer and Seed Script
Executes auth_schema.sql and seeds institutional users, roles, and encrypted biometric templates.
"""

import os
import math
import random
import uuid
from app.db.database import get_connection
from app.services.security import hash_password, encrypt_biometric_vector


def generate_deterministic_vector(seed_name: str, dimension: int = 128) -> list[float]:
    """
    Returns the enrolled vector for the user from auth_biometric_credentials if available,
    or generates a reproducible normalized vector of the specified dimension.
    """
    try:
        from psycopg.rows import dict_row
        from app.services.security import decrypt_biometric_vector
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT b.encrypted_embedding, b.encryption_nonce, b.encryption_tag, b.embedding_dimension
                    FROM auth_biometric_credentials b
                    JOIN auth_users u ON u.id = b.user_id
                    WHERE u.employee_id = %s AND b.status = 'ACTIVE';
                    """,
                    (seed_name.strip(),)
                )
                row = cur.fetchone()
                if row:
                    return decrypt_biometric_vector(
                        bytes(row["encrypted_embedding"]),
                        bytes(row["encryption_nonce"]),
                        bytes(row["encryption_tag"]),
                        dimension=row["embedding_dimension"]
                    )
    except Exception:
        pass

    rng = random.Random(seed_name)
    raw = [rng.gauss(0.0, 1.0) for _ in range(dimension)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]



def init_and_seed_auth():
    print("[MuleGuard Auth Init] Connecting to PostgreSQL database...")
    schema_path = os.path.join(os.path.dirname(__file__), "auth_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection() as conn:
        with conn.cursor() as cur:
            print("[MuleGuard Auth Init] Executing auth_schema.sql...")
            cur.execute(schema_sql)

            # 1. Seed Roles
            roles = [
                ("bank_investigator", "Bank Investigator", "Lead fraud investigator with case analysis and transaction scrutiny permissions"),
                ("bank_compliance", "Bank Compliance Officer", "Senior compliance and AML officer with filing and executive override permissions"),
                ("internal_team", "Platform Administrator", "Internal MuleGuard core platform engineer and system health administrator")
            ]
            for r_id, r_name, r_desc in roles:
                cur.execute(
                    """
                    INSERT INTO auth_roles (id, name, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description;
                    """,
                    (r_id, r_name, r_desc)
                )

            # 2. Seed Default Institutional Employees
            default_password = "Password@123"
            hashed_pwd = hash_password(default_password)
            print(f"[MuleGuard Auth Init] Generated Argon2id hash for default password.")

            users = [
                {
                    "id": "u-inv-001",
                    "employee_id": "MG-INV-001",
                    "email": "j.doe@muleguard.bank",
                    "full_name": "J. Doe",
                    "department": "Fraud Investigations",
                    "title": "Bank Investigator",
                    "role_id": "bank_investigator"
                },
                {
                    "id": "u-cmp-001",
                    "employee_id": "MG-CMP-001",
                    "email": "a.kumar@muleguard.bank",
                    "full_name": "A. Kumar",
                    "department": "AML Compliance",
                    "title": "Bank Compliance Officer",
                    "role_id": "bank_compliance"
                },
                {
                    "id": "u-adm-001",
                    "employee_id": "MG-ADM-001",
                    "email": "t.miller@muleguard.bank",
                    "full_name": "T. Miller",
                    "department": "Core Platform Engineering",
                    "title": "Platform Administrator",
                    "role_id": "internal_team"
                }
            ]

            for u in users:
                cur.execute(
                    """
                    INSERT INTO auth_users (
                        id, employee_id, email, full_name, department, title, role_id, password_hash, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                    ON CONFLICT (employee_id) DO UPDATE
                    SET email = EXCLUDED.email, full_name = EXCLUDED.full_name, title = EXCLUDED.title,
                        role_id = EXCLUDED.role_id, password_hash = EXCLUDED.password_hash, status = 'ACTIVE';
                    """,
                    (
                        u["id"], u["employee_id"], u["email"], u["full_name"],
                        u["department"], u["title"], u["role_id"], hashed_pwd
                    )
                )

                # 3. Seed Encrypted Biometric Template Vector
                vector = generate_deterministic_vector(u["employee_id"])
                ciphertext, nonce, tag = encrypt_biometric_vector(vector)
                bio_id = f"bio-{u['id']}"

                cur.execute(
                    """
                    INSERT INTO auth_biometric_credentials (
                        id, user_id, algorithm, embedding_dimension, encrypted_embedding,
                        encryption_nonce, encryption_tag, enrollment_quality_score, status
                    ) VALUES (%s, %s, 'facenet-512', 512, %s, %s, %s, 99.20, 'ACTIVE')
                    ON CONFLICT (user_id) DO UPDATE
                    SET encrypted_embedding = EXCLUDED.encrypted_embedding,
                        encryption_nonce = EXCLUDED.encryption_nonce,
                        encryption_tag = EXCLUDED.encryption_tag,
                        status = 'ACTIVE';
                    """,
                    (bio_id, u["id"], ciphertext, nonce, tag)
                )

            conn.commit()
            print("[MuleGuard Auth Init] Initialized and seeded auth tables successfully!")


if __name__ == "__main__":
    init_and_seed_auth()
