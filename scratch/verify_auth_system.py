"""
MuleGuard Authentication & Biometric Verification System Test Runner
Validates end-to-end institutional authentication directly via HTTP and database:
- Argon2id password verification
- Liveness challenge detection & Presentation Attack Detection (PAD)
- Encrypted biometric vector retrieval & cosine similarity matching
- Session cookie creation & revocation in PostgreSQL
- RBAC authorization
- Audit logging verification
"""

import json
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

from app.db.database import get_connection
from app.db.init_auth_db import generate_deterministic_vector

BASE_URL = "http://127.0.0.1:8000"


class APIClient:
    def __init__(self):
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

    def request(self, method, path, data=None):
        url = f"{BASE_URL}{path}"
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

        try:
            with self.opener.open(req) as resp:
                resp_body = resp.read().decode("utf-8")
                return {
                    "status_code": resp.status,
                    "data": json.loads(resp_body) if resp_body else {},
                    "cookies": {c.name: c.value for c in self.cookie_jar}
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            return {
                "status_code": e.code,
                "data": json.loads(err_body) if err_body.startswith("{") else {"detail": err_body},
                "cookies": {c.name: c.value for c in self.cookie_jar}
            }


def test_auth_system():
    print("====================================================")
    print("MULEGUARD INSTITUTIONAL AUTHENTICATION TEST SUITE")
    print("====================================================")

    client = APIClient()
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

    # ----------------------------------------------------
    # TEST 1: Stage 1 - Invalid Credentials Handling
    # ----------------------------------------------------
    print("\n[Test 1] Stage 1 - Credential Rejections & Protections...")
    res = client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "NON_EXISTENT", "password": "Any"})
    assert_test(res["status_code"] == 401, "Nonexistent employee should be rejected with 401")

    res = client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "MG-INV-001", "password": "WrongPassword"})
    assert_test(res["status_code"] == 401, "Invalid password should be rejected with 401")

    # ----------------------------------------------------
    # TEST 2: Stage 1 - Successful Password Verification
    # ----------------------------------------------------
    print("\n[Test 2] Stage 1 - Argon2id Password Verification...")
    res = client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "MG-INV-001", "password": "Password@123"})
    assert_test(res["status_code"] == 200, "Valid credentials should return 200 OK")
    data = res["data"]
    assert_test(data.get("success") is True, "Response should report success = true")
    assert_test("challenge" in data, "Response must include liveness challenge")
    assert_test("challenge_token" in data["challenge"], "Challenge must have ephemeral challenge_token")
    assert_test(data.get("role_id") == "bank_investigator", "Role must be returned from DB: bank_investigator")
    
    challenge_token = data["challenge"]["challenge_token"]

    # ----------------------------------------------------
    # TEST 3: Stage 2 - Liveness Rejection (PAD)
    # ----------------------------------------------------
    print("\n[Test 3] Stage 2 - Presentation Attack & Liveness Detection...")
    probe_vec = generate_deterministic_vector("MG-INV-001")
    bad_liveness = {
        "action_performed": "WRONG_ACTION_SPOOF",
        "confidence": 0.99,
        "timestamps": [1.0, 2.0, 3.0]
    }
    res = client.request("POST", "/api/v1/auth/stage2-verify-face", {
        "challenge_token": challenge_token,
        "probe_vector": probe_vec,
        "liveness_proof": bad_liveness
    })
    assert_test(res["status_code"] in [400, 401], "Mismatching liveness challenge action must be rejected with 400 or 401")

    # ----------------------------------------------------
    # TEST 4: Stage 2 - Biometric Face Mismatch Rejection
    # ----------------------------------------------------
    print("\n[Test 4] Stage 2 - Biometric Cosine Similarity Mismatch...")
    # Re-issue challenge token
    res_stg1 = client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "MG-INV-001", "password": "Password@123"})
    challenge2 = res_stg1["data"]["challenge"]
    
    # Send a mismatched face vector
    mismatched_vector = generate_deterministic_vector("MG-ADM-001")
    valid_liveness = {
        "action_performed": challenge2["challenge_action"],
        "confidence": 0.98,
        "timestamps": [10.0, 10.5, 11.0]
    }
    res_mismatch = client.request("POST", "/api/v1/auth/stage2-verify-face", {
        "challenge_token": challenge2["challenge_token"],
        "probe_vector": mismatched_vector,
        "liveness_proof": valid_liveness
    })
    assert_test(res_mismatch["status_code"] == 401, "Face mismatch (cosine similarity below threshold) must be rejected with 401")

    # ----------------------------------------------------
    # TEST 5: Stage 2 - Successful Biometric Match & Session Creation
    # ----------------------------------------------------
    print("\n[Test 5] Stage 2 - Successful Face Verification & Session Cookie...")
    res_stg1 = client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "MG-INV-001", "password": "Password@123"})
    challenge3 = res_stg1["data"]["challenge"]

    matching_vector = generate_deterministic_vector("MG-INV-001")
    valid_liveness = {
        "action_performed": challenge3["challenge_action"],
        "confidence": 0.98,
        "timestamps": [20.0, 20.5, 21.0]
    }

    res_auth = client.request("POST", "/api/v1/auth/stage2-verify-face", {
        "challenge_token": challenge3["challenge_token"],
        "probe_vector": matching_vector,
        "liveness_proof": valid_liveness
    })
    assert_test(res_auth["status_code"] == 200, "Valid face and liveness must return 200 OK")
    auth_data = res_auth["data"]
    assert_test(auth_data["user"]["role"] == "bank_investigator", "User role must be bank_investigator")
    assert_test("muleguard_sid" in res_auth["cookies"], "Response must include HttpOnly muleguard_sid cookie")
    assert_test(auth_data["redirect_url"] == "/frontend/bank/investigator/dashboard.html", "Redirect URL must route to investigator dashboard")

    # ----------------------------------------------------
    # TEST 6: Session Verification via /api/v1/auth/me
    # ----------------------------------------------------
    print("\n[Test 6] Session Integrity & /api/v1/auth/me Profile Check...")
    res_me = client.request("GET", "/api/v1/auth/me")
    assert_test(res_me["status_code"] == 200, "Authenticated session must return 200 from /me")
    me_data = res_me["data"]
    assert_test(me_data["user"]["employee_id"] == "MG-INV-001", "Session profile employee_id must match MG-INV-001")
    assert_test(me_data["user"]["role"] == "bank_investigator", "Session profile role must match bank_investigator")

    # ----------------------------------------------------
    # TEST 7: Compliance Officer Login Flow & Role Routing
    # ----------------------------------------------------
    print("\n[Test 7] Compliance Officer Persona Authentication...")
    cmp_client = APIClient()
    cmp_stg1 = cmp_client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "MG-CMP-001", "password": "Password@123"})
    assert_test(cmp_stg1["status_code"] == 200, "Compliance officer credentials must succeed")
    cmp_challenge = cmp_stg1["data"]["challenge"]

    cmp_vec = generate_deterministic_vector("MG-CMP-001")
    cmp_liveness = {
        "action_performed": cmp_challenge["challenge_action"],
        "confidence": 0.97,
        "timestamps": [30.0, 30.5, 31.0]
    }
    cmp_auth = cmp_client.request("POST", "/api/v1/auth/stage2-verify-face", {
        "challenge_token": cmp_challenge["challenge_token"],
        "probe_vector": cmp_vec,
        "liveness_proof": cmp_liveness
    })
    assert_test(cmp_auth["status_code"] == 200, "Compliance face verification must return 200 OK")
    assert_test(cmp_auth["data"]["user"]["role"] == "bank_compliance", "Backend must assign bank_compliance role")
    assert_test(cmp_auth["data"]["redirect_url"] == "/frontend/bank/compliance/dashboard.html", "Redirect URL must route to compliance dashboard")

    # ----------------------------------------------------
    # TEST 8: Platform Administrator Authentication
    # ----------------------------------------------------
    print("\n[Test 8] Internal Team / Admin Persona Authentication...")
    adm_client = APIClient()
    adm_stg1 = adm_client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "MG-ADM-001", "password": "Password@123"})
    assert_test(adm_stg1["status_code"] == 200, "Admin credentials must succeed")
    adm_challenge = adm_stg1["data"]["challenge"]

    adm_vec = generate_deterministic_vector("MG-ADM-001")
    adm_liveness = {
        "action_performed": adm_challenge["challenge_action"],
        "confidence": 0.99,
        "timestamps": [40.0, 40.5, 41.0]
    }
    adm_auth = adm_client.request("POST", "/api/v1/auth/stage2-verify-face", {
        "challenge_token": adm_challenge["challenge_token"],
        "probe_vector": adm_vec,
        "liveness_proof": adm_liveness
    })
    assert_test(adm_auth["status_code"] == 200, "Admin face verification must return 200 OK")
    assert_test(adm_auth["data"]["user"]["role"] == "internal_team", "Backend must assign internal_team role")
    assert_test(adm_auth["data"]["redirect_url"] == "/frontend/internal/dashboard.html", "Redirect URL must route to internal dashboard")

    # ----------------------------------------------------
    # TEST 9: Logout & Session Revocation
    # ----------------------------------------------------
    print("\n[Test 9] Logout & Database Session Revocation...")
    res_logout = client.request("POST", "/api/v1/auth/logout")
    assert_test(res_logout["status_code"] == 200, "Logout must return 200 OK")
    
    # /me should now fail with 401
    res_me_revoked = client.request("GET", "/api/v1/auth/me")
    assert_test(res_me_revoked["status_code"] == 401, "Subsequent /me must return 401 Unauthorized after logout")

    # ----------------------------------------------------
    # TEST 10: PostgreSQL Audit Trail Verification
    # ----------------------------------------------------
    print("\n[Test 10] Immutable PostgreSQL Audit Trail Inspection...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT event_type, outcome, failure_reason FROM auth_audit_log ORDER BY id DESC LIMIT 20;")
            logs = cur.fetchall()
            event_types = {row[0] for row in logs}
            
            assert_test("STAGE1_SUCCESS" in event_types, "Audit log must contain STAGE1_SUCCESS")
            assert_test("LOGIN_FAILED" in event_types, "Audit log must contain LOGIN_FAILED")
            assert_test("FACE_VERIFICATION_SUCCESS" in event_types, "Audit log must contain FACE_VERIFICATION_SUCCESS")
            assert_test("LOGIN_SUCCESS" in event_types, "Audit log must contain LOGIN_SUCCESS")
            assert_test("LOGOUT" in event_types, "Audit log must contain LOGOUT")

    print("\n====================================================")
    print(f"ALL AUTH TESTS PASSED: {passed_tests}/{total_tests} PASS")
    print("====================================================")


if __name__ == "__main__":
    test_auth_system()
