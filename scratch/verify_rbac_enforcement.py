"""
MuleGuard RBAC & Backend Authorization Test Runner
Verifies:
- Unauthenticated requests return 401 across all sensitive endpoints
- Authenticated Investigator requests allowed on investigator endpoints
- Authenticated Compliance requests allowed on compliance endpoints
- Authenticated Admin requests allowed on admin endpoints
- Unauthorized role access returns 403 Forbidden
- Logout and session revocation properly invalidates subsequent API requests
"""

import json
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

from app.db.database import get_connection
from app.db.init_auth_db import generate_deterministic_vector

BASE_URL = "http://127.0.0.1:8000"


class AuthenticatedClient:
    def __init__(self):
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

    def request(self, method, path, data=None):
        url = f"{BASE_URL}{path}"
        headers = {"Content-Type": "application/json", "X-Forwarded-For": "10.99.1.1"}
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

    def login(self, employee_id, password="Password@123"):
        # Stage 1
        res1 = self.request("POST", "/api/v1/auth/stage1-login", {"employee_id": employee_id, "password": password})
        if res1["status_code"] != 200:
            raise RuntimeError(f"Login stage 1 failed: {res1}")

        ch = res1["data"]["challenge"]
        vec = generate_deterministic_vector(employee_id)
        now = 100.0
        proof = {
            "action_performed": ch["challenge_action"],
            "confidence": 0.98,
            "timestamps": [now, now + 0.5, now + 1.0]
        }

        # Stage 2
        res2 = self.request("POST", "/api/v1/auth/stage2-verify-face", {
            "challenge_token": ch["challenge_token"],
            "probe_vector": vec,
            "liveness_proof": proof
        })
        if res2["status_code"] != 200:
            raise RuntimeError(f"Login stage 2 failed: {res2}")
        return res2["data"]


def test_rbac():
    print("====================================================")
    print("MULEGUARD BACKEND RBAC ENFORCEMENT VERIFICATION")
    print("====================================================")

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

    # 1. Unauthenticated Request
    print("\n[Section 1] Unauthenticated Requests Return 401...")
    anon = AuthenticatedClient()
    res = anon.request("GET", "/api/v1/accounts")
    assert_test(res["status_code"] == 401, "Unauthenticated accounts request must return 401")

    res = anon.request("GET", "/api/v1/transactions")
    assert_test(res["status_code"] == 401, "Unauthenticated transactions request must return 401")

    res = anon.request("GET", "/api/v1/alerts")
    assert_test(res["status_code"] == 401, "Unauthenticated alerts request must return 401")

    # 2. Authenticated Investigator Access
    print("\n[Section 2] Authenticated Investigator Access...")
    inv = AuthenticatedClient()
    inv.login("MG-INV-001")
    
    res = inv.request("GET", "/api/v1/accounts")
    assert_test(res["status_code"] == 200 and len(res["data"]) > 0, "Investigator can access /accounts (200 OK)")

    res = inv.request("GET", "/api/v1/transactions")
    assert_test(res["status_code"] == 200 and len(res["data"]) > 0, "Investigator can access /transactions (200 OK)")

    res = inv.request("GET", "/api/v1/alerts")
    assert_test(res["status_code"] == 200 and len(res["data"]) > 0, "Investigator can access /alerts (200 OK)")

    res = inv.request("GET", "/api/v1/cases")
    assert_test(res["status_code"] == 200, "Investigator can access /cases (200 OK)")

    res = inv.request("GET", "/api/v1/risk/summary")
    assert_test(res["status_code"] == 200 and "total_accounts" in res["data"], "Investigator can access /risk/summary (200 OK)")

    res = inv.request("GET", "/api/v1/watchlists")
    assert_test(res["status_code"] == 200, "Investigator can access /watchlists (200 OK)")

    res = inv.request("GET", "/api/v1/networks")
    assert_test(res["status_code"] == 200, "Investigator can access /networks (200 OK)")

    # 3. Investigator Unauthorized Endpoint Rejections (403 Forbidden)
    print("\n[Section 3] Investigator Unauthorized Role Rejections (403 Forbidden)...")
    res = inv.request("GET", "/api/v1/decisions")
    assert_test(res["status_code"] == 403, "Investigator forbidden from Compliance-only /decisions (403 Forbidden)")

    res = inv.request("GET", "/api/v1/rules")
    assert_test(res["status_code"] == 403, "Investigator forbidden from Admin-only /rules (403 Forbidden)")

    res = inv.request("GET", "/api/v1/audit-logs")
    assert_test(res["status_code"] == 403, "Investigator forbidden from /audit-logs (403 Forbidden)")

    # 4. Authenticated Compliance Officer Access
    print("\n[Section 4] Authenticated Compliance Officer Access...")
    cmp_user = AuthenticatedClient()
    cmp_user.login("MG-CMP-001")

    res = cmp_user.request("GET", "/api/v1/accounts")
    assert_test(res["status_code"] == 200, "Compliance can access /accounts (200 OK)")

    res = cmp_user.request("GET", "/api/v1/decisions")
    assert_test(res["status_code"] == 200, "Compliance can access /decisions (200 OK)")

    res = cmp_user.request("GET", "/api/v1/audit-logs")
    assert_test(res["status_code"] == 200, "Compliance can access /audit-logs (200 OK)")

    # Compliance Forbidden from Admin-only /rules
    res = cmp_user.request("GET", "/api/v1/rules")
    assert_test(res["status_code"] == 403, "Compliance forbidden from Admin-only /rules (403 Forbidden)")

    # 5. Authenticated Platform Administrator Access
    print("\n[Section 5] Authenticated Platform Admin Access...")
    adm = AuthenticatedClient()
    adm.login("MG-ADM-001")

    res = adm.request("GET", "/api/v1/accounts")
    assert_test(res["status_code"] == 200, "Admin can access /accounts (200 OK)")

    res = adm.request("GET", "/api/v1/rules")
    assert_test(res["status_code"] == 200, "Admin can access /rules (200 OK)")

    res = adm.request("GET", "/api/v1/audit-logs")
    assert_test(res["status_code"] == 200, "Admin can access /audit-logs (200 OK)")

    # Admin Forbidden from Operational Banking alerts, cases, decisions
    res = adm.request("GET", "/api/v1/alerts")
    assert_test(res["status_code"] == 403, "Admin forbidden from operational /alerts (403 Forbidden)")

    res = adm.request("GET", "/api/v1/cases")
    assert_test(res["status_code"] == 403, "Admin forbidden from operational /cases (403 Forbidden)")

    res = adm.request("GET", "/api/v1/decisions")
    assert_test(res["status_code"] == 403, "Admin forbidden from compliance-only /decisions (403 Forbidden)")

    # 6. Logout and Session Revocation
    print("\n[Section 6] Logout and Subsequent Session Rejection...")
    res = inv.request("POST", "/api/v1/auth/logout")
    assert_test(res["status_code"] == 200, "Investigator logout returns 200 OK")

    res = inv.request("GET", "/api/v1/accounts")
    assert_test(res["status_code"] == 401, "Subsequent /accounts request after logout returns 401 Unauthorized")

    # 7. Revoked / Expired Session Validation
    print("\n[Section 7] Revoked / Expired Session DB Validation...")
    temp_client = AuthenticatedClient()
    temp_client.login("MG-INV-001")
    # Verify works
    res = temp_client.request("GET", "/api/v1/accounts")
    assert_test(res["status_code"] == 200, "Active session accesses /accounts")

    # Manually revoke in database to test revocation detection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE auth_sessions SET is_revoked = TRUE, revocation_reason = 'SECURITY_REVOKE' WHERE user_id = 'u-inv-001';")
            conn.commit()

    res = temp_client.request("GET", "/api/v1/accounts")
    assert_test(res["status_code"] == 401, "Manually revoked session is rejected with 401 Unauthorized")

    print("\n====================================================")
    print(f"ALL RBAC VERIFICATION TESTS PASSED: {passed_tests}/{total_tests} PASS")
    print("====================================================")


if __name__ == "__main__":
    test_rbac()
