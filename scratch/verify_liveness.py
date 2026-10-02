"""
MuleGuard Presentation Attack Detection (PAD) & Active Liveness Verification Suite
Tests the complete PAD & Liveness pipeline:
1. Passive PAD via MiniFASNetV2 (OpenCV DNN):
   - Genuine live face acceptance (Obama, Messi)
   - Obvious presentation attack / digital spoof rejection (face1.jpg)
   - Bounding box boundary padding robustness
2. Active Liveness via YuNet Facial Landmarks:
   - Geometric yaw and pitch ratio calculation
   - Rejection of static single-frame presentation attacks (STATIC_IMAGE_DETECTED)
   - Verification of active challenges: TURN_RIGHT, TURN_LEFT, NOD
   - Rejection of incorrect physical movement (WRONG_MOVEMENT)
3. Full Stage 2 Authentication Integration via API:
   - Challenge token generation & single-use consumption
   - Expiration validation (180s TTL)
   - Replay protection against token reuse
   - No-face and multi-face rejection
   - Presentation attack rejection (HTTP 400 PRESENTATION_ATTACK_DETECTED)
   - Wrong movement rejection (HTTP 400 LIVENESS_FAILED)
   - End-to-end success with genuine live sequence + SFace match
   - Security auditing in PostgreSQL (zero raw images or vectors logged)
"""

import os
import sys
import base64
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

import cv2
import numpy as np

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
    req_headers = {"User-Agent": "MuleGuard-Liveness-Verifier/1.0"}
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


def bytes_to_base64(img_bytes: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode("utf-8")


def get_fresh_challenge(emp_id: str, pwd: str, client_ip: str) -> tuple[str, str, str]:
    _, data, _ = make_request(
        "POST", "/api/v1/auth/stage1-login",
        {"employee_id": emp_id, "password": pwd},
        headers={"X-Forwarded-For": client_ip}
    )
    return (
        data["challenge"]["challenge_token"],
        data["challenge"]["challenge_action"],
        data["challenge"]["instruction"]
    )


def run_tests():
    print("=" * 75)
    print("MuleGuard — Presentation Attack Detection (PAD) & Liveness Test Suite")
    print("=" * 75)

    obama_path = str(BASE_DIR / "data" / "models" / "face_obama.jpg")
    messi_path = str(BASE_DIR / "data" / "models" / "messi_face.jpg")
    spoof_path = str(BASE_DIR / "data" / "models" / "screen_replay_spoof.jpg") # Screen presentation attack with bezel

    obama_img = cv2.imread(obama_path)
    messi_img = cv2.imread(messi_path)
    spoof_img = cv2.imread(spoof_path)

    # -------------------------------------------------------------------------
    # Group 1: MiniFASNetV2 Passive Presentation Attack Detection (PAD)
    # -------------------------------------------------------------------------
    print("\n--- Group 1: Passive PAD (MiniFASNetV2) Unit Tests ---")
    from app.services.face_engine import (
        get_face_models,
        evaluate_passive_pad,
        extract_landmark_pose,
        verify_active_challenge_movement,
        detect_face_and_pose_from_bytes
    )

    detector, _ = get_face_models()

    # Test 1.1: Live Face Sample (Obama)
    h_o, w_o, _ = obama_img.shape
    detector.setInputSize((w_o, h_o))
    _, faces_o = detector.detect(obama_img)
    is_live_o, cls_o, conf_o = evaluate_passive_pad(obama_img, faces_o[0][:4])
    record_result(
        "1.1 Genuine Live Face Acceptance (Obama)",
        is_live_o is True and cls_o == "LIVE_FACE" and conf_o >= 0.90,
        f"Class: {cls_o}, Confidence: {conf_o:.4f}"
    )

    # Test 1.2: Live Face Sample (Messi)
    h_m, w_m, _ = messi_img.shape
    detector.setInputSize((w_m, h_m))
    _, faces_m = detector.detect(messi_img)
    is_live_m, cls_m, conf_m = evaluate_passive_pad(messi_img, faces_m[0][:4])
    record_result(
        "1.2 Genuine Live Face Acceptance (Messi)",
        is_live_m is True and cls_m == "LIVE_FACE" and conf_m >= 0.90,
        f"Class: {cls_m}, Confidence: {conf_m:.4f}"
    )

    # Test 1.3: Digital Screen / Replay Spoof Sample (face1.jpg)
    h_s, w_s, _ = spoof_img.shape
    detector.setInputSize((w_s, h_s))
    _, faces_s = detector.detect(spoof_img)
    is_live_s, cls_s, conf_s = evaluate_passive_pad(spoof_img, faces_s[0][:4])
    record_result(
        "1.3 Presentation Attack Detection Rejection (face1.jpg)",
        is_live_s is False and cls_s in ["SCREEN_REPLAY_SPOOF", "PHOTO_SPOOF"],
        f"Blocked as: {cls_s}, Attack Confidence: {conf_s:.4f}"
    )

    # Test 1.4: Extreme border padding test
    # Simulate face near image border to ensure zero padding does not crash
    border_face = [5, 5, 120, 120]
    is_live_b, cls_b, conf_b = evaluate_passive_pad(obama_img, border_face)
    record_result(
        "1.4 Border Crop & Zero-Padding Robustness",
        cls_b in ["LIVE_FACE", "SCREEN_REPLAY_SPOOF", "PHOTO_SPOOF"],
        f"Result: {cls_b}, Handled boundary without overflow"
    )

    # -------------------------------------------------------------------------
    # Group 2: YuNet Facial Landmark Active Liveness Geometry
    # -------------------------------------------------------------------------
    print("\n--- Group 2: Active Landmark Movement Geometry Tests ---")

    pose_obama = extract_landmark_pose(faces_o[0])
    record_result(
        "2.1 Landmark Pose Ratios Extraction",
        "yaw_ratio" in pose_obama and "pitch_ratio" in pose_obama and "norm_yaw" in pose_obama,
        f"Yaw: {pose_obama['yaw_ratio']}, Pitch: {pose_obama['pitch_ratio']}, NormYaw: {pose_obama['norm_yaw']}"
    )

    # Test 2.2: Static Single-Frame Presentation Rejection
    # Submitting identical frames for baseline and action
    is_live_static, reason_static, _ = verify_active_challenge_movement(
        pose_obama, pose_obama, "TURN_RIGHT"
    )
    record_result(
        "2.2 Static Presentation Rejection",
        is_live_static is False and "STATIC_IMAGE_DETECTED" in reason_static,
        f"Correctly flagged: {reason_static}"
    )

    # Test 2.3: Correct Turn Right Movement
    pose_right = dict(pose_obama)
    pose_right["yaw_ratio"] = 1.80
    pose_right["norm_yaw"] = -0.12
    is_live_tr, reason_tr, _ = verify_active_challenge_movement(pose_obama, pose_right, "TURN_RIGHT")
    record_result(
        "2.3 Correct Movement Verification (TURN_RIGHT)",
        is_live_tr is True,
        f"Status: {reason_tr}"
    )

    # Test 2.4: Correct Turn Left Movement
    pose_left = dict(pose_obama)
    pose_left["yaw_ratio"] = 0.65
    pose_left["norm_yaw"] = 0.12
    is_live_tl, reason_tl, _ = verify_active_challenge_movement(pose_obama, pose_left, "TURN_LEFT")
    record_result(
        "2.4 Correct Movement Verification (TURN_LEFT)",
        is_live_tl is True,
        f"Status: {reason_tl}"
    )

    # Test 2.5: Correct Nod Movement
    pose_nod = dict(pose_obama)
    pose_nod["pitch_ratio"] = 0.68
    is_live_nod, reason_nod, _ = verify_active_challenge_movement(pose_obama, pose_nod, "NOD")
    record_result(
        "2.5 Correct Movement Verification (NOD)",
        is_live_nod is True,
        f"Status: {reason_nod}"
    )

    # Test 2.6: Wrong Physical Movement Rejection
    # Turned right when asked to turn left
    is_wrong_mv, reason_wrong, _ = verify_active_challenge_movement(pose_obama, pose_right, "TURN_LEFT")
    record_result(
        "2.6 Wrong Movement Direction Rejection",
        is_wrong_mv is False and "WRONG_MOVEMENT" in reason_wrong,
        f"Flagged: {reason_wrong}"
    )

    # -------------------------------------------------------------------------
    # Group 3: Stage 2 Biometric & PAD Authentication API
    # -------------------------------------------------------------------------
    print("\n--- Group 3: Authentication Flow & Attack Resistance Tests ---")
    emp_adm = "MG-ADM-001"
    pwd = "Password@123"

    # Test 3.1: Stage 1 Challenge Generation
    token_31, action_31, instr_31 = get_fresh_challenge(emp_adm, pwd, "10.0.1.1")
    record_result(
        "3.1 Stage 1 Active Challenge Generation",
        token_31 is not None and action_31 in ["TURN_RIGHT", "TURN_LEFT", "NOD"],
        f"Issued action: {action_31} ('{instr_31}')"
    )

    # Test 3.2: Rejection of Single Static Frame without movement sequence
    token_32, action_32, _ = get_fresh_challenge(emp_adm, pwd, "10.0.1.2")
    obama_b64 = load_image_base64(obama_path)
    status_32, body_32, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_32,
            "image_base64": obama_b64
            # Omitting baseline_image_base64 and liveness_proof
        },
        headers={"X-Forwarded-For": "10.0.1.2"}
    )
    record_result(
        "3.2 Static Single-Frame Rejection (HTTP 400)",
        status_32 == 400 and "requires a frame sequence" in body_32.get("detail", ""),
        f"Status: {status_32}, Detail: {body_32.get('detail')}"
    )

    # Test 3.3: Presentation Attack Rejection via API (Spoof Face)
    token_33, action_33, _ = get_fresh_challenge(emp_adm, pwd, "10.0.1.3")
    spoof_b64 = load_image_base64(spoof_path)
    status_33, body_33, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_33,
            "image_base64": spoof_b64,
            "baseline_image_base64": obama_b64
        },
        headers={"X-Forwarded-For": "10.0.1.3"}
    )
    record_result(
        "3.3 Presentation Attack Rejection (HTTP 400)",
        status_33 == 400 and "Presentation attack detected" in body_33.get("detail", ""),
        f"Status: {status_33}, Detail: {body_33.get('detail')}"
    )

    # Test 3.4: No-Face Frame Rejection
    token_34, action_34, _ = get_fresh_challenge(emp_adm, pwd, "10.0.1.4")
    blank_canvas = np.zeros((300, 300, 3), dtype=np.uint8)
    _, blank_bytes = cv2.imencode(".jpg", blank_canvas)
    blank_b64 = bytes_to_base64(blank_bytes.tobytes())
    status_34, body_34, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_34,
            "image_base64": blank_b64,
            "baseline_image_base64": obama_b64
        },
        headers={"X-Forwarded-For": "10.0.1.4"}
    )
    record_result(
        "3.4 No-Face Detection Rejection (HTTP 400)",
        status_34 == 400 and "NO_FACE_DETECTED" in body_34.get("detail", ""),
        f"Status: {status_34}, Detail: {body_34.get('detail')}"
    )

    # Test 3.5: Multiple Faces Frame Rejection
    token_35, action_35, _ = get_fresh_challenge(emp_adm, pwd, "10.0.1.5")
    multi_canvas = np.hstack([obama_img, cv2.resize(messi_img, (obama_img.shape[1], obama_img.shape[0]))])
    _, multi_bytes = cv2.imencode(".jpg", multi_canvas)
    multi_b64 = bytes_to_base64(multi_bytes.tobytes())
    status_35, body_35, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_35,
            "image_base64": multi_b64,
            "baseline_image_base64": obama_b64
        },
        headers={"X-Forwarded-For": "10.0.1.5"}
    )
    record_result(
        "3.5 Multi-Face Detection Rejection (HTTP 400)",
        status_35 == 400 and "MULTIPLE_FACES_DETECTED" in body_35.get("detail", ""),
        f"Status: {status_35}, Detail: {body_35.get('detail')}"
    )

    # Test 3.6: Wrong Movement Direction via API
    # Create action frame with wrong movement (same as baseline = static)
    token_36, action_36, _ = get_fresh_challenge(emp_adm, pwd, "10.0.1.6")
    status_36, body_36, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_36,
            "baseline_image_base64": obama_b64,
            "image_base64": obama_b64 # Static photo presentation!
        },
        headers={"X-Forwarded-For": "10.0.1.6"}
    )
    record_result(
        "3.6 Static Photo Attack Rejection (HTTP 400)",
        status_36 == 400 and "STATIC_IMAGE_DETECTED" in body_36.get("detail", ""),
        f"Status: {status_36}, Detail: {body_36.get('detail')}"
    )

    # Test 3.7: Reused Challenge Token Protection (Anti-Replay)
    status_37, body_37, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": token_36, # Reusing token_36
            "baseline_image_base64": obama_b64,
            "image_base64": obama_b64
        },
        headers={"X-Forwarded-For": "10.0.1.7"}
    )
    record_result(
        "3.7 Reused Challenge Replay Protection (HTTP 401)",
        status_37 == 401 and "expired or already consumed" in body_37.get("detail", ""),
        f"Status: {status_37}, Detail: {body_37.get('detail')}"
    )

    # Test 3.8: Expired Challenge Token Rejection
    status_38, body_38, _ = make_request(
        "POST", "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": "expired_or_fake_token_xyz_999",
            "image_base64": obama_b64
        },
        headers={"X-Forwarded-For": "10.0.1.8"}
    )
    record_result(
        "3.8 Expired / Unknown Challenge Token Rejection (HTTP 401)",
        status_38 == 401,
        f"Status: {status_38}, Detail: {body_38.get('detail')}"
    )

    # Test 3.9: End-to-End Success: Live Frame + Valid Action + Matching SFace Face
    # Temporarily backup current enrolled template for MG-ADM-001 so live user's face is never lost
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM auth_biometric_credentials WHERE user_id = (SELECT id FROM auth_users WHERE employee_id = %s);",
                (emp_adm,)
            )
            saved_bio_row = cur.fetchone()

    # Temporarily enroll obama_b64 for test 3.9
    make_request(
        "POST", "/api/v1/auth/enroll-face",
        {"employee_id": emp_adm, "password": pwd, "image_base64": obama_b64},
        headers={"X-Forwarded-For": "10.0.1.9"}
    )

    try:
        token_39, action_39, _ = get_fresh_challenge(emp_adm, pwd, "10.0.1.9")
        while action_39 not in ["TURN_RIGHT", "TURN_LEFT"]:
            token_39, action_39, _ = get_fresh_challenge(emp_adm, pwd, "10.0.1.9")

        h_ob, w_ob, _ = obama_img.shape
        center_ob = (w_ob // 2, h_ob // 2)

        if action_39 == "TURN_RIGHT":
            M_act = cv2.getRotationMatrix2D(center_ob, 6, 1.0)
        else:  # TURN_LEFT
            M_act = cv2.getRotationMatrix2D(center_ob, -6, 1.0)

        action_img_ob = cv2.warpAffine(obama_img, M_act, (w_ob, h_ob))
        _, action_bytes_ob = cv2.imencode(".jpg", action_img_ob)
        action_b64_ob = bytes_to_base64(action_bytes_ob.tobytes())

        status_39, body_39, headers_39 = make_request(
            "POST", "/api/v1/auth/stage2-verify-face",
            {
                "challenge_token": token_39,
                "baseline_image_base64": obama_b64,
                "image_base64": action_b64_ob
            },
            headers={"X-Forwarded-For": "10.0.1.9"}
        )
        set_cookie = headers_39.get("set-cookie") or headers_39.get("Set-Cookie", "")
        has_sid = "muleguard_sid=" in set_cookie
        record_result(
            "3.9 Full PAD + Active Liveness + SFace Verification Success",
            status_39 == 200 and body_39.get("success") is True and has_sid,
            f"Authenticated: {body_39.get('user', {}).get('name')}, Role: {body_39.get('user', {}).get('role')}, Session Cookie Issued"
        )
    finally:
        # Restore user's real enrolled biometric template
        if saved_bio_row:
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
                            saved_bio_row["encrypted_embedding"],
                            saved_bio_row["encryption_nonce"],
                            saved_bio_row["encryption_tag"],
                            saved_bio_row["embedding_dimension"],
                            saved_bio_row["enrollment_quality_score"],
                            saved_bio_row["status"],
                            saved_bio_row["user_id"]
                        )
                    )
                    conn.commit()

    # -------------------------------------------------------------------------
    # Group 4: Security Audit Trail & Zero Biometric Leakage
    # -------------------------------------------------------------------------
    print("\n--- Group 4: Security Audit Logging ---")
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT event_type, employee_id, outcome, failure_reason, details
                FROM auth_audit_log
                WHERE event_type IN ('PAD_ATTACK_DETECTED', 'LIVENESS_FAILED', 'FACE_VERIFICATION_SUCCESS')
                ORDER BY event_timestamp DESC
                LIMIT 15;
                """
            )
            audit_records = cur.fetchall()

    pad_logged = any(r["event_type"] == "PAD_ATTACK_DETECTED" for r in audit_records)
    liveness_logged = any(r["event_type"] == "LIVENESS_FAILED" for r in audit_records)
    success_logged = any(r["event_type"] == "FACE_VERIFICATION_SUCCESS" for r in audit_records)

    raw_images_leaked = any("data:image" in str(r.get("details")) or len(str(r.get("details"))) > 500 for r in audit_records)
    vectors_leaked = any("probe_vector" in str(r.get("details")) for r in audit_records)

    record_result(
        "4.1 Security Audit Events Recorded",
        pad_logged and liveness_logged and success_logged,
        f"Verified events: PAD_ATTACK_DETECTED={pad_logged}, LIVENESS_FAILED={liveness_logged}, FACE_VERIFICATION_SUCCESS={success_logged}"
    )

    record_result(
        "4.2 Biometric Privacy & Zero-Frame Storage Policy",
        not raw_images_leaked and not vectors_leaked,
        "Confirmed: Zero raw camera frames and zero biometric vectors in database audit logs"
    )

    print("\n" + "=" * 75)
    print(f"LIVENESS SUITE TOTAL: {PASSED + FAILED} | PASSED: {PASSED} | FAILED: {FAILED}")
    print("=" * 75)

    if FAILED > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
