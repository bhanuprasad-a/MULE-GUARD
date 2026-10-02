"""
MuleGuard IP Rate Limiting Verification Suite
Tests:
- Configurable environment variable limits
- Normal authentication requests pass
- Repeated attempts from same IP trigger HTTP 429 with Retry-After header
- Different IPs remain unblocked (isolation)
- Employee account lockout (5 failed attempts) operates independently
- Session creation and audit logging for rate limit events
"""

import os
import json
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

from app.db.database import get_connection
from app.db.init_auth_db import generate_deterministic_vector
from app.services.rate_limiter import auth_rate_limiter, get_rate_limit_config

BASE_URL = "http://127.0.0.1:8000"


def send_request(path, data, ip_header=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if ip_header:
        headers["X-Forwarded-For"] = ip_header

    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return {
                "status_code": resp.status,
                "data": json.loads(resp_body) if resp_body else {},
                "headers": dict(resp.headers)
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {
            "status_code": e.code,
            "data": json.loads(err_body) if err_body.startswith("{") else {"detail": err_body},
            "headers": dict(e.headers)
        }


def test_rate_limiting():
    print("====================================================")
    print("MULEGUARD IP-LEVEL RATE LIMITING VERIFICATION")
    print("====================================================")

    max_reqs, window_secs = get_rate_limit_config()
    print(f"Active Rate Limit Configuration: {max_reqs} requests per {window_secs} seconds")

    total_tests = 0
    passed_tests = 0

    def assert_test(cond, title):
        nonlocal total_tests, passed_tests
        total_tests += 1
        if cond:
            passed_tests += 1
            print(f"  [OK] PASS: {title}")
        else:
            print(f"  [FAIL] FAIL: {title}")
            assert False, title

    # Clean in-memory limiter before test
    auth_rate_limiter.clear()

    # 1. Normal Login Succeeded Under Limit
    print("\n[Test 1] Normal Authentication Request Under Limit...")
    client_ip_a = "192.168.1.100"
    res = send_request(
        "/api/v1/auth/stage1-login",
        {"employee_id": "MG-INV-001", "password": "Password@123"},
        ip_header=client_ip_a
    )
    assert_test(res["status_code"] == 200, "Initial request from IP A returns 200 OK")
    assert_test(res["data"].get("success") is True, "Stage 1 reports success = true")

    # 2. Exhaust Limit on IP A
    print(f"\n[Test 2] Exceeding Rate Limit on IP A (Sending {max_reqs} requests)...")
    for i in range(max_reqs - 1):
        r = send_request(
            "/api/v1/auth/stage1-login",
            {"employee_id": "MG-INV-001", "password": "Password@123"},
            ip_header=client_ip_a
        )
        assert_test(r["status_code"] == 200, f"Request {i+2}/{max_reqs} within limit succeeds")

    # Next request must be blocked with 429
    res_blocked = send_request(
        "/api/v1/auth/stage1-login",
        {"employee_id": "MG-INV-001", "password": "Password@123"},
        ip_header=client_ip_a
    )
    assert_test(res_blocked["status_code"] == 429, "Request exceeding limit returns HTTP 429 Too Many Requests")
    headers_lower = {k.lower(): v for k, v in res_blocked["headers"].items()}
    assert_test("retry-after" in headers_lower, "HTTP 429 response includes Retry-After header")
    retry_after_val = headers_lower["retry-after"]
    assert_test(int(retry_after_val) > 0, f"Retry-After is valid positive integer: {retry_after_val}s")

    # 3. Different IP B is NOT Blocked (Isolation)
    print("\n[Test 3] Different IP B Isolation Verification...")
    client_ip_b = "192.168.1.101"
    res_b = send_request(
        "/api/v1/auth/stage1-login",
        {"employee_id": "MG-INV-001", "password": "Password@123"},
        ip_header=client_ip_b
    )
    assert_test(res_b["status_code"] == 200, "Request from distinct IP B succeeds while IP A is blocked")

    # 4. Stage 2 Biometrics Rate Limiting
    print("\n[Test 4] Stage 2 Endpoint Rate Limit Verification...")
    # IP A attempts Stage 2
    res_stg2_blocked = send_request(
        "/api/v1/auth/stage2-verify-face",
        {
            "challenge_token": "dummy_token",
            "probe_vector": [0.0] * 512,
            "liveness_proof": {"action_performed": "BLINK", "confidence": 0.9, "timestamps": [1, 2, 3]}
        },
        ip_header=client_ip_a
    )
    assert_test(res_stg2_blocked["status_code"] == 429, "Stage 2 from rate-limited IP A is also blocked with 429")

    # 5. Independent Per-Employee 5-Failure Lockout Check
    print("\n[Test 5] Independent Employee Account Lockout Operating Correctly...")
    lockout_ip = "192.168.1.200"
    # Ensure fresh IP
    auth_rate_limiter.reset_for_ip(lockout_ip)

    # Use MG-ADM-001 for lockout test
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE auth_users SET failed_login_attempts = 0, status = 'ACTIVE', locked_until = NULL WHERE employee_id = 'MG-ADM-001';")
            conn.commit()

    for attempt in range(1, 6):
        r_fail = send_request(
            "/api/v1/auth/stage1-login",
            {"employee_id": "MG-ADM-001", "password": "WrongPassword!"},
            ip_header=lockout_ip
        )
        assert_test(r_fail["status_code"] == 401, f"Failed attempt {attempt}/5 returns 401 Unauthorized")

    # 6th attempt should be blocked by account lockout (not IP rate limit)
    r_locked = send_request(
        "/api/v1/auth/stage1-login",
        {"employee_id": "MG-ADM-001", "password": "Password@123"},
        ip_header=lockout_ip
    )
    assert_test(r_locked["status_code"] == 401 and "locked" in r_locked["data"]["detail"].lower(), "Account locked independently of IP rate limit")

    # Reset admin account
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE auth_users SET failed_login_attempts = 0, status = 'ACTIVE', locked_until = NULL WHERE employee_id = 'MG-ADM-001';")
            conn.commit()

    # 6. Audit Trail for Rate Limit Event
    print("\n[Test 6] Immutable PostgreSQL Audit Trail for RATE_LIMIT_EXCEEDED...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT event_type, outcome, failure_reason, ip_address FROM auth_audit_log WHERE event_type = 'RATE_LIMIT_EXCEEDED' ORDER BY id DESC LIMIT 1;")
            audit_entry = cur.fetchone()
            assert_test(audit_entry is not None, "Audit log records RATE_LIMIT_EXCEEDED")
            assert_test(audit_entry[1] == "BLOCKED", "Audit outcome is BLOCKED")
            assert_test(audit_entry[2] == "IP_RATE_LIMIT_EXCEEDED", "Audit failure reason is IP_RATE_LIMIT_EXCEEDED")

    # Clean up rate limiter
    auth_rate_limiter.clear()

    print("\n====================================================")
    print(f"ALL RATE LIMITING TESTS PASSED: {passed_tests}/{total_tests} PASS")
    print("====================================================")


if __name__ == "__main__":
    test_rate_limiting()
