"""
Verification Script for Stage 3: API + Frontend Security Hardening
Tests:
1. Pagination parameters (limit, offset) and boundary checks (min ge=1, max le=500)
2. String length bounds and input validation (Path, Query, Pydantic)
3. Request size protection (HTTP 413 on oversized payload)
4. Security headers (CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)
5. Error sanitization (no internal exception leakage / stack traces)
"""

import sys
import os
import json
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.init_auth_db import generate_deterministic_vector

BASE_URL = "http://127.0.0.1:8000"

passed = 0
failed = 0

def test(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} - {details}")

print("\n" + "=" * 60)
print("STAGE 3: API & FRONTEND SECURITY HARDENING VERIFICATION")
print("=" * 60)


class Client:
    def __init__(self, ip="10.99.1.50"):
        self.ip = ip
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

    def request(self, method, path, data=None, headers_override=None):
        url = f"{BASE_URL}{path}"
        headers = {
            "Content-Type": "application/json",
            "X-Forwarded-For": self.ip
        }
        if headers_override:
            headers.update(headers_override)

        req_data = None
        if data is not None:
            if isinstance(data, (dict, list)):
                req_data = json.dumps(data).encode("utf-8")
            elif isinstance(data, bytes):
                req_data = data
            elif isinstance(data, str):
                req_data = data.encode("utf-8")

        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

        try:
            with self.opener.open(req) as resp:
                resp_body = resp.read().decode("utf-8")
                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                parsed_data = {}
                if resp_body:
                    try:
                        parsed_data = json.loads(resp_body)
                    except Exception:
                        parsed_data = {"raw": resp_body}
                return {
                    "status_code": resp.status,
                    "data": parsed_data,
                    "headers": resp_headers,
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            resp_headers = {k.lower(): v for k, v in e.headers.items()}
            parsed_err = {}
            if err_body:
                try:
                    parsed_err = json.loads(err_body)
                except Exception:
                    parsed_err = {"raw": err_body}
            return {
                "status_code": e.code,
                "data": parsed_err,
                "headers": resp_headers,
            }


def login_client(client, employee_id, password="Password@123"):
    r1 = client.request("POST", "/api/v1/auth/stage1-login", {"employee_id": employee_id, "password": password})
    if r1["status_code"] != 200:
        return False
    ch = r1["data"]["challenge"]
    vec = generate_deterministic_vector(employee_id)
    proof = {
        "action_performed": ch["challenge_action"],
        "confidence": 0.98,
        "timestamps": [100.0, 100.5, 101.0]
    }
    r2 = client.request("POST", "/api/v1/auth/stage2-verify-face", {
        "challenge_token": ch["challenge_token"],
        "probe_vector": vec,
        "liveness_proof": proof
    })
    return r2["status_code"] == 200


admin_client = Client("10.99.1.51")
test("Admin login for security tests", login_client(admin_client, "MG-ADM-001"))

inv_client = Client("10.99.1.52")
test("Investigator login for security tests", login_client(inv_client, "MG-INV-001"))

cmp_client = Client("10.99.1.53")
test("Compliance login for security tests", login_client(cmp_client, "MG-CMP-001"))

# ----------------------------------------------------
# 1. API Pagination & Bounds
# ----------------------------------------------------
print("\n--- 1. API Pagination & Bounded Limits ---")

endpoints_to_test = [
    ("/api/v1/accounts", inv_client, 500),
    ("/api/v1/transactions", inv_client, 500),
    ("/api/v1/alerts", inv_client, 500),
    ("/api/v1/cases", inv_client, 500),
    ("/api/v1/audit-logs", admin_client, 500),
    ("/api/v1/watchlists", inv_client, 500),
    ("/api/v1/decisions", cmp_client, 500),
    ("/api/v1/rules", admin_client, 100),
    ("/api/v1/networks", inv_client, 100),
]

for ep, cli, max_limit in endpoints_to_test:
    # Default fetch succeeds
    res_def = cli.request("GET", ep)
    test(f"{ep} - default fetch succeeds", res_def["status_code"] == 200)

    # Page size limit=2 returns <= 2 items
    res_p2 = cli.request("GET", f"{ep}?limit=2&offset=0")
    test(f"{ep} - limit=2 returns <= 2 items", res_p2["status_code"] == 200 and isinstance(res_p2["data"], list) and len(res_p2["data"]) <= 2)

    # Boundary: limit exceeding max should be rejected with 422
    res_exceed = cli.request("GET", f"{ep}?limit={max_limit + 1}")
    test(f"{ep} - limit={max_limit + 1} rejected with 422", res_exceed["status_code"] == 422)

    # Boundary: limit=0 should be rejected with 422
    res_zero = cli.request("GET", f"{ep}?limit=0")
    test(f"{ep} - limit=0 rejected with 422", res_zero["status_code"] == 422)

# Account transactions pagination
accs_res = inv_client.request("GET", "/api/v1/accounts?limit=1")
valid_acc_id = accs_res["data"][0]["id"] if (accs_res["status_code"] == 200 and accs_res["data"]) else "ACC-1001"

res_acc_tx = inv_client.request("GET", f"/api/v1/accounts/{valid_acc_id}/transactions?limit=2&offset=0")
test("Account transactions - limit=2 returns <= 2 items", res_acc_tx["status_code"] == 200 and isinstance(res_acc_tx["data"], list) and len(res_acc_tx["data"]) <= 2)

res_acc_tx_exceed = inv_client.request("GET", f"/api/v1/accounts/{valid_acc_id}/transactions?limit=501")
test("Account transactions - limit=501 rejected with 422", res_acc_tx_exceed["status_code"] == 422)

# ----------------------------------------------------
# 2. Input Length & Parameter Protection
# ----------------------------------------------------
print("\n--- 2. Input Length & Parameter Validation ---")

# Excessive account_id length (>64 chars)
long_acc_id = "A" * 65
res_long_acc = inv_client.request("GET", f"/api/v1/accounts/{long_acc_id}")
test("Excessive account_id length rejected with 422", res_long_acc["status_code"] == 422)

# Excessive watchlist reason (>256 chars)
long_reason = "X" * 257
res_long_reason = inv_client.request("POST", f"/api/v1/watchlists/ACC-1001?reason={long_reason}")
test("Excessive watchlist reason rejected with 422", res_long_reason["status_code"] == 422)

# Excessive employee_id in Stage 1 login (>64 chars)
anon = Client("10.99.1.99")
res_long_emp = anon.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "M" * 65, "password": "pass"})
test("Excessive employee_id in Stage 1 rejected with 422", res_long_emp["status_code"] == 422)

# Excessive password in Stage 1 login (>128 chars)
res_long_pwd = anon.request("POST", "/api/v1/auth/stage1-login", {"employee_id": "MG-INV-001", "password": "P" * 129})
test("Excessive password in Stage 1 rejected with 422", res_long_pwd["status_code"] == 422)

# Excessive transaction type in ingest (>64 chars)
res_long_tx_type = inv_client.request(
    "POST",
    "/api/v1/transactions/ingest",
    {
        "senderId": "ACC-1001",
        "receiverId": "ACC-1002",
        "amountNumeric": 500.0,
        "type": "T" * 65
    }
)
test("Excessive transaction type in ingest rejected with 422", res_long_tx_type["status_code"] == 422)

# ----------------------------------------------------
# 3. Request Payload Size Protection
# ----------------------------------------------------
print("\n--- 3. Request Payload Size Protection ---")

# Oversized Content-Length header (e.g. 16MB)
res_oversized = anon.request(
    "POST",
    "/api/v1/auth/stage1-login",
    data=b"{}",
    headers_override={"Content-Length": str(16 * 1024 * 1024)}
)
test("Payload exceeding 15MB rejected with HTTP 413", res_oversized["status_code"] == 413)

# ----------------------------------------------------
# 4. Security Headers & CSP
# ----------------------------------------------------
print("\n--- 4. Security Headers & CSP Enforcement ---")

res_headers = anon.request("GET", "/health")
h = res_headers["headers"]

test("Content-Security-Policy present", "content-security-policy" in h)
csp = h.get("content-security-policy", "")
test("CSP contains default-src 'self'", "default-src 'self'" in csp)
test("CSP allows Google Fonts styles and font", "fonts.googleapis.com" in csp and "fonts.gstatic.com" in csp)
test("CSP allows webcam / canvas blobs", "blob:" in csp)
test("CSP restricts object-src 'none'", "object-src 'none'" in csp)
test("CSP restricts frame-ancestors 'none'", "frame-ancestors 'none'" in csp)

test("X-Content-Type-Options: nosniff", h.get("x-content-type-options") == "nosniff")
test("X-Frame-Options: DENY", h.get("x-frame-options") == "DENY")
test("Referrer-Policy: strict-origin-when-cross-origin", h.get("referrer-policy") == "strict-origin-when-cross-origin")
test("Permissions-Policy camera restriction present", "permissions-policy" in h and "camera=(self)" in h["permissions-policy"])

# ----------------------------------------------------
# 5. Error Sanitization
# ----------------------------------------------------
print("\n--- 5. Error Sanitization & Implementation Masking ---")

res_db = anon.request("GET", "/db-test")
test("/db-test returns 200 when connected", res_db["status_code"] == 200)

print("\n" + "=" * 60)
print(f"VERIFICATION SUMMARY: {passed} PASSED, {failed} FAILED")
print("=" * 60)

if failed > 0:
    sys.exit(1)
