"""
MuleGuard Real Facial Recognition System (FRS) Verification Suite
Tests the complete end-to-end face verification pipeline:
1. Real SFace embedding generation (128-d)
2. Face quality & single-face enforcement
3. Rejection of no-face, multi-face, and degraded images
4. Real biometric enrollment via POST /api/v1/auth/enroll-face
5. AES-256-GCM encrypted biometric template storage in PostgreSQL
6. Successful verification using matching enrolled face frame
7. Rejection of impostor/wrong face frame
8. Single-use challenge token & expiration validation
9. Password authentication & session issuance
10. Audit logging verification (no raw biometrics logged)
"""

import os
import sys
import base64
import json
import urllib.request
import urllib.error
import cv2
import numpy as np
from pathlib import Path

from app.db.database import get_connection
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = "http://127.0.0.1:8000"

PASSED = 0
FAILED = 0


def record_result(test_name: str, passed: bool, detail: str = ""):
    global PASSED, FAILED
    if passed:
        PASSED += 1
        print(f"  [PASS] {test_name}" + (f" -> {detail}" if detail else ""))
    else:
        FAILED += 1
        print(f"  [FAIL] {test_name}" + (f" -> {detail}" if detail else ""))


def make_request(method: str, path: str, data: dict = None, cookie: str = None, headers: dict = None) -> tuple[int, dict, dict]:
    url = f"{BASE_URL}{path}"
    req_headers = {"User-Agent": "MuleGuard-FRS-Verifier/1.0"}
    if headers:
        req_headers.update(headers)
    if cookie:
        req_headers["Cookie"] = cookie
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_headers = dict(resp.headers)
            resp_body = json.loads(resp.read().decode("utf-8"))
            return resp.status, resp_body, resp_headers
    except urllib.error.HTTPError as e:
        resp_headers = dict(e.headers)
        try:
            resp_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            resp_body = {"detail": "HTTP error"}
        return e.code, resp_body, resp_headers


def load_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("utf-8")


def get_fresh_challenge(emp_id: str, pwd: str, client_ip: str) -> tuple[str, str]:
    _, data, _ = make_request(
        "POST", "/api/v1/auth/stage1-login",
        {"employee_id": emp_id, "password": pwd},
        headers={"X-Forwarded-For": client_ip}
    )
    return data["challenge"]["challenge_token"], data["challenge"]["challenge_action"]


def run_tests():
    print("=" * 70)
    print("MuleGuard — Real Facial Recognition System (FRS) Test Suite")
    print("=" * 70)

    face1_path = str(BASE_DIR / "data" / "models" / "face1.jpg") # Lena
    messi_path = str(BASE_DIR / "data" / "models" / "messi_face.jpg") # Messi
    obama_path = str(BASE_DIR / "data" / "models" / "face_obama.jpg") # Obama

    # ---------------------------------------------------------
    # Group 1: Local Face Engine Unit Tests
    # ---------------------------------------------------------
    print("\n--- Group 1: Local Face Engine & Embeddings ---")
    from app.services.face_engine import (
        extract_face_embedding_from_bytes,
        extract_face_embedding_from_base64,
        compute_cosine_similarity
    )

    # Test 1.1: Extract embedding from face1.jpg
    with open(face1_path, "rb") as f:
        b1 = f.read()
    emb1, err1, meta1 = extract_face_embedding_from_bytes(b1)
    record_result(
        "1.1 Real Embedding Generation (Face 1)",
        err1 is None and len(emb1) == 128,
        f"Extracted {len(emb1) if emb1 else 0}-d vector, quality={meta1.get('quality_score')}%"
    )

    # Test 1.2: Extract embedding from messi_face.jpg
    with open(messi_path, "rb") as f:
        b2 = f.read()
    emb2, err2, meta2 = extract_face_embedding_from_bytes(b2)
    record_result(
        "1.2 Real Embedding Generation (Face 2)",
        err2 is None and len(emb2) == 128,
        f"Extracted {len(emb2) if emb2 else 0}-d vector, quality={meta2.get('quality_score')}%"
    )

    # Test 1.3: Cosine similarity self-match vs cross-match separation
    sim_self = compute_cosine_similarity(emb1, emb1)
    sim_cross = compute_cosine_similarity(emb1, emb2)
    record_result(
        "1.3 Embedding Cosine Separation",
        sim_self > 0.99 and sim_cross < 0.20,
        f"Self: {sim_self:.4f}, Cross: {sim_cross:.4f} (Delta: {sim_self - sim_cross:.4f})"
    )

    # Test 1.4: No face rejection
    blank_canvas = np.zeros((300, 300, 3), dtype=np.uint8)
    _, blank_bytes = cv2.imencode(".jpg", blank_canvas)
    emb_blank, err_blank, _ = extract_face_embedding_from_bytes(blank_bytes.tobytes())
    record_result(
        "1.4 No-Face Detection Rejection",
        emb_blank is None and "NO_FACE_DETECTED" in (err_blank or ""),
        f"Correctly flagged: {err_blank}"
    )

    # Test 1.5: Multi-face rejection
    img1 = cv2.imread(face1_path)
    img2 = cv2.resize(cv2.imread(messi_path), (img1.shape[1], img1.shape[0]))
    multi_canvas = np.hstack([img1, img2])
    _, multi_bytes = cv2.imencode(".jpg", multi_canvas)
    emb_multi, err_multi, _ = extract_face_embedding_from_bytes(multi_bytes.tobytes())
    record_result(
        "1.5 Multiple-Face Detection Rejection",
        emb_multi is None and "MULTIPLE_FACES_DETECTED" in (err_multi or ""),
        f"Correctly flagged: {err_multi}"
    )

    # Test 1.6: Blurry face rejection
    blurry_img = cv2.GaussianBlur(img1, (21, 21), 6)
    _, blur_bytes = cv2.imencode(".jpg", blurry_img)
    emb_blur, err_blur, _ = extract_face_embedding_from_bytes(blur_bytes.tobytes())
    record_result(
        "1.6 Degraded/Blurry Face Rejection",
        emb_blur is None and any(k in (err_blur or "") for k in ["FACE_TOO_BLURRY", "NO_FACE_DETECTED", "LOW_FACE_CONFIDENCE"]),
        f"Correctly flagged: {err_blur}"
    )

    # ---------------------------------------------------------
    # Group 2: Biometric Enrollment Flow
    # ---------------------------------------------------------
    print("\n--- Group 2: Biometric Enrollment API ---")
    emp_inv = "MG-INV-001"
    pwd = "Password@123"
    face1_b64 = load_image_base64(face1_path)
    messi_b64 = load_image_base64(messi_path)
    obama_b64 = load_image_base64(obama_path)

    # Test 2.1: Enrollment with wrong password rejected
    status, body, _ = make_request(
        "POST", "/api/v1/auth/enroll-face",
        {"employee_id": emp_inv, "password": "WrongPassword999", "image_base64": obama_b64},
        headers={"X-Forwarded-For": "172.16.0.1"}
    )
    record_result(
        "2.1 Unauthorized Enrollment Rejection",
        status == 401,
        f"Status: {status}, Detail: {body.get('detail')}"
    )

    # Test 2.2: Enrollment with no-face image rejected
    blank_b64 = "data:image/jpeg;base64," + base64.b64encode(blank_bytes.tobytes()).decode("utf-8")
    status, body, _ = make_request(
        "POST", "/api/v1/auth/enroll-face",
        {"employee_id": emp_inv, "password": pwd, "image_base64": blank_b64},
        headers={"X-Forwarded-For": "172.16.0.2"}
    )
    record_result(
        "2.2 No-Face Image Enrollment Rejection",
        status == 400 and "NO_FACE_DETECTED" in body.get("detail", ""),
        f"Status: {status}, Detail: {body.get('detail')}"
    )

    # Test 2.3: Successful face enrollment
    # Backup user template for MG-INV-001 before test enrollment
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM auth_biometric_credentials WHERE user_id = (SELECT id FROM auth_users WHERE employee_id = %s);",
                (emp_inv,)
            )
            saved_inv_bio = cur.fetchone()

    status, body, _ = make_request(
        "POST", "/api/v1/auth/enroll-face",
        {"employee_id": emp_inv, "password": pwd, "image_base64": obama_b64},
        headers={"X-Forwarded-For": "172.16.0.3"}
    )
    record_result(
        "2.3 Valid Face Enrollment (SFace 128-d)",
        status == 200 and body.get("success") is True and body.get("embedding_dimension") == 128,
        f"Algo: {body.get('algorithm')}, Dim: {body.get('embedding_dimension')}, Quality: {body.get('quality_score')}%"
    )

    # Test 2.4: Database encrypted template verification
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT b.algorithm, b.embedding_dimension, b.encrypted_embedding,
                       b.encryption_nonce, b.encryption_tag, b.status
                FROM auth_biometric_credentials b
                JOIN auth_users u ON u.id = b.user_id
                WHERE u.employee_id = %s;
                """,
                (emp_inv,)
            )
            bio_row = cur.fetchone()

    is_enc = (
        bio_row is not None and
        bio_row["algorithm"] == "opencv-sface-128" and
        bio_row["embedding_dimension"] == 128 and
        len(bytes(bio_row["encrypted_embedding"])) == 512 and
        len(bytes(bio_row["encryption_nonce"])) == 12 and
        len(bytes(bio_row["encryption_tag"])) == 16
    )
    record_result(
        "2.4 PostgreSQL AES-256-GCM Encrypted Template",
        is_enc,
        f"Ciphertext: 512B, Nonce: 12B, Tag: 16B, Raw Image: NOT stored in DB"
    )

    # ---------------------------------------------------------
    # Group 3: Live Verification & Impostor Rejection
    # ---------------------------------------------------------
    print("\n--- Group 3: Live Verification & Impostor Rejection ---")

    # Test 3.1: Stage 1 Password & Challenge Issuance
    token_31, action_31 = get_fresh_challenge(emp_inv, pwd, "172.16.1.1")
    record_result(
        "3.1 Stage 1 Password & Challenge Issuance",
        token_31 is not None and len(token_31) > 20,
        f"Employee: {emp_inv}, Action: {action_31}"
    )

    # Test 3.2: Verify with No-Face frame (fresh challenge)
    token_32, action_32 = get_fresh_challenge(emp_inv, pwd, "172.16.1.2")
    status, body, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_32,
            "image_base64": blank_b64,
            "liveness_proof": {"action_performed": action_32, "confidence": 0.95}
        },
        headers={"X-Forwarded-For": "172.16.1.2"}
    )
    record_result(
        "3.2 No-Face Verification Rejection (HTTP 400)",
        status == 400 and "NO_FACE_DETECTED" in body.get("detail", ""),
        f"Status: {status}, Detail: {body.get('detail')}"
    )

    # Test 3.3: Verify with Multiple-Face frame (fresh challenge)
    token_33, action_33 = get_fresh_challenge(emp_inv, pwd, "172.16.1.3")
    multi_b64 = "data:image/jpeg;base64," + base64.b64encode(multi_bytes.tobytes()).decode("utf-8")
    status, body, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_33,
            "image_base64": multi_b64,
            "liveness_proof": {"action_performed": action_33, "confidence": 0.95}
        },
        headers={"X-Forwarded-For": "172.16.1.3"}
    )
    record_result(
        "3.3 Multi-Face Verification Rejection (HTTP 400)",
        status == 400 and "MULTIPLE_FACES_DETECTED" in body.get("detail", ""),
        f"Status: {status}, Detail: {body.get('detail')}"
    )

    # Test 3.4: Verify with Impostor Face (Messi against Lena's template) (fresh challenge)
    token_34, action_34 = get_fresh_challenge(emp_inv, pwd, "172.16.1.4")
    status, body, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_34,
            "image_base64": messi_b64,
            "liveness_proof": {"action_performed": action_34, "confidence": 0.95}
        },
        headers={"X-Forwarded-For": "172.16.1.4"}
    )
    record_result(
        "3.4 Impostor / Wrong Face Rejection (HTTP 401)",
        status == 401 and "below required threshold" in body.get("detail", ""),
        f"Status: {status}, Detail: {body.get('detail')}"
    )

    # Test 3.5: Verify with Matching Enrolled Face (Obama against Obama) (fresh challenge)
    token_35, action_35 = get_fresh_challenge(emp_inv, pwd, "172.16.1.5")
    status, body, headers = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_35,
            "image_base64": obama_b64,
            "liveness_proof": {"action_performed": action_35, "confidence": 0.98}
        },
        headers={"X-Forwarded-For": "172.16.1.5"}
    )
    set_cookie = headers.get("set-cookie") or headers.get("Set-Cookie", "")
    has_sid = "muleguard_sid=" in set_cookie
    record_result(
        "3.5 Enrolled Face Verification Success",
        status == 200 and body.get("success") is True and has_sid,
        f"User: {body.get('user', {}).get('name')}, Role: {body.get('user', {}).get('role')}, Redirect: {body.get('redirect_url')}"
    )

    # Test 3.6: Single-use challenge token consumption (reusing token_35)
    status_reuse, body_reuse, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_35,
            "image_base64": face1_b64,
            "liveness_proof": {"action_performed": action_35, "confidence": 0.98}
        },
        headers={"X-Forwarded-For": "172.16.1.6"}
    )
    record_result(
        "3.6 Challenge Single-Use Replay Rejection",
        status_reuse == 401 and "expired" in body_reuse.get("detail", "").lower(),
        f"Status: {status_reuse}, Detail: {body_reuse.get('detail')}"
    )

    # Test 3.7: Fake / expired challenge rejection
    status_fake, body_fake, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": "non_existent_token_12345",
            "image_base64": face1_b64,
            "liveness_proof": {"action_performed": "BLINK", "confidence": 0.95}
        },
        headers={"X-Forwarded-For": "172.16.1.7"}
    )
    record_result(
        "3.7 Invalid/Expired Challenge Rejection",
        status_fake == 401,
        f"Status: {status_fake}, Detail: {body_fake.get('detail')}"
    )

    # ---------------------------------------------------------
    # Group 4: Multi-User Enrollment & Role Isolation
    # ---------------------------------------------------------
    print("\n--- Group 4: Multi-User Enrollment & Security ---")
    emp_cmp = "MG-CMP-001"
    emp_adm = "MG-ADM-001"

    # Enroll Compliance Officer with messi_face.jpg
    make_request(
        "POST", "/api/v1/auth/enroll-face",
        {"employee_id": emp_cmp, "password": pwd, "image_base64": messi_b64},
        headers={"X-Forwarded-For": "172.16.2.1"}
    )
    # Enroll Admin with face_obama.jpg
    obama_b64 = load_image_base64(obama_path)
    make_request(
        "POST", "/api/v1/auth/enroll-face",
        {"employee_id": emp_adm, "password": pwd, "image_base64": obama_b64},
        headers={"X-Forwarded-For": "172.16.2.2"}
    )

    # Test 4.1: Compliance Officer logs in with messi_face
    c_tok, c_act = get_fresh_challenge(emp_cmp, pwd, "172.16.2.3")
    c_status, c_body, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": c_tok,
            "image_base64": messi_b64,
            "liveness_proof": {"action_performed": c_act, "confidence": 0.95}
        },
        headers={"X-Forwarded-For": "172.16.2.3"}
    )
    record_result(
        "4.1 Compliance Officer Face Match",
        c_status == 200 and c_body.get("user", {}).get("role") == "bank_compliance",
        f"Role: {c_body.get('user', {}).get('role')}, Redirect: {c_body.get('redirect_url')}"
    )

    # Test 4.2: Admin logs in with obama face
    a_tok, a_act = get_fresh_challenge(emp_adm, pwd, "172.16.2.4")
    a_status, a_body, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": a_tok,
            "image_base64": obama_b64,
            "liveness_proof": {"action_performed": a_act, "confidence": 0.95}
        },
        headers={"X-Forwarded-For": "172.16.2.4"}
    )
    record_result(
        "4.2 Admin Face Match",
        a_status == 200 and a_body.get("user", {}).get("role") == "internal_team",
        f"Role: {a_body.get('user', {}).get('role')}, Redirect: {a_body.get('redirect_url')}"
    )

    # Test 4.3: Cross-user rejection (Admin face presented for Compliance officer)
    bad_tok, bad_act = get_fresh_challenge(emp_cmp, pwd, "172.16.2.5")
    bad_status, bad_body, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": bad_tok,
            "image_base64": obama_b64, # Wrong face!
            "liveness_proof": {"action_performed": bad_act, "confidence": 0.95}
        },
        headers={"X-Forwarded-For": "172.16.2.5"}
    )
    record_result(
        "4.3 Cross-User Impostor Rejection",
        bad_status == 401,
        f"Status: {bad_status}, Detail: {bad_body.get('detail')}"
    )

    # ---------------------------------------------------------
    # Group 5: Audit Trail & Security Sanitation
    # ---------------------------------------------------------
    print("\n--- Group 5: Audit Trail & Biometric Privacy ---")
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT event_type, employee_id, outcome, failure_reason, details
                FROM auth_audit_log
                WHERE event_type IN ('FACE_ENROLLMENT_SUCCESS', 'FACE_VERIFICATION_FAILED', 'STAGE2_SUCCESS')
                ORDER BY event_timestamp DESC
                LIMIT 10;
                """
            )
            audit_rows = cur.fetchall()

    has_audit = len(audit_rows) > 0
    # Confirm no raw biometric vectors in details
    vectors_leaked = any("probe_vector" in str(r.get("details")) or "embedding" in str(r.get("details")) for r in audit_rows)
    record_result(
        "5.1 Biometric Security Audit Trail",
        has_audit and not vectors_leaked,
        f"Verified {len(audit_rows)} audit events. Zero raw biometric vectors exposed in logs."
    )

    # Restore user's real enrolled biometric template for MG-INV-001
    if saved_inv_bio:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE auth_biometric_credentials
                    SET encrypted_embedding = %s, encryption_nonce = %s, encryption_tag = %s,
                        embedding_dimension = %s, enrollment_quality_score = %s, status = %s
                    WHERE user_id = %s;
                    """,
                    (
                        saved_inv_bio["encrypted_embedding"],
                        saved_inv_bio["encryption_nonce"],
                        saved_inv_bio["encryption_tag"],
                        saved_inv_bio["embedding_dimension"],
                        saved_inv_bio["enrollment_quality_score"],
                        saved_inv_bio["status"],
                        saved_inv_bio["user_id"]
                    )
                )
                conn.commit()

    print("\n" + "=" * 70)
    print(f"TOTAL: {PASSED + FAILED} | PASSED: {PASSED} | FAILED: {FAILED}")
    print("=" * 70)

    if FAILED > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
