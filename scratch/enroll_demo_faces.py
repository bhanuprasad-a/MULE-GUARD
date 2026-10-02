"""
MuleGuard Demo User Real Biometric Enrollment Script
Enrolls authentic 128-d SFace embeddings for the three institutional demo users:
- MG-INV-001 (J. Doe, Bank Investigator) -> enrolled with face1.jpg
- MG-CMP-001 (A. Kumar, Compliance Officer) -> enrolled with messi_face.jpg
- MG-ADM-001 (T. Miller, Platform Administrator) -> enrolled with face_obama.jpg

All templates are encrypted using AES-256-GCM and stored in auth_biometric_credentials.
Raw images are NEVER stored in the database.
"""

import os
import base64
from pathlib import Path

from app.services.auth_service import enroll_employee_face
from app.db.database import get_connection
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent.parent

DEMO_ENROLLMENTS = [
    {
        "employee_id": "MG-INV-001",
        "password": "Password@123",
        "image_path": str(BASE_DIR / "data" / "models" / "face1.jpg"),
        "label": "J. Doe (Bank Investigator)"
    },
    {
        "employee_id": "MG-CMP-001",
        "password": "Password@123",
        "image_path": str(BASE_DIR / "data" / "models" / "messi_face.jpg"),
        "label": "A. Kumar (Compliance Officer)"
    },
    {
        "employee_id": "MG-ADM-001",
        "password": "Password@123",
        "image_path": str(BASE_DIR / "data" / "models" / "face_obama.jpg"),
        "label": "T. Miller (Platform Administrator)"
    }
]


def enroll_all_demo_users():
    print("=" * 70)
    print("MuleGuard — Enrolling Real SFace Biometric Templates for Demo Users")
    print("=" * 70)

    for item in DEMO_ENROLLMENTS:
        emp_id = item["employee_id"]
        pwd = item["password"]
        img_path = item["image_path"]
        label = item["label"]

        if not os.path.exists(img_path):
            print(f"[ERROR] Image file not found: {img_path}")
            continue

        with open(img_path, "rb") as f:
            img_bytes = f.read()

        b64_str = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode("utf-8")

        result = enroll_employee_face(
            employee_id=emp_id,
            password=pwd,
            image_base64=b64_str,
            ip_address="127.0.0.1",
            user_agent="MuleGuard-Enrollment-Script/1.0"
        )

        if result.get("success"):
            print(f"[OK] {emp_id} ({label}): Enrolled {result['algorithm']} ({result['embedding_dimension']}-d) | Quality: {result['quality_score']}%")
        else:
            print(f"[FAILED] {emp_id} ({label}): {result.get('error')}")

    print("\nVerifying database auth_biometric_credentials status:")
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT u.employee_id, u.full_name, b.algorithm, b.embedding_dimension,
                       b.enrollment_quality_score, b.status, length(b.encrypted_embedding) as enc_bytes
                FROM auth_biometric_credentials b
                JOIN auth_users u ON u.id = b.user_id
                ORDER BY u.employee_id;
                """
            )
            for row in cur.fetchall():
                print(f"  * {row['employee_id']} ({row['full_name']}): algo={row['algorithm']}, dim={row['embedding_dimension']}, enc_len={row['enc_bytes']}B, quality={row['enrollment_quality_score']}")


if __name__ == "__main__":
    enroll_all_demo_users()
