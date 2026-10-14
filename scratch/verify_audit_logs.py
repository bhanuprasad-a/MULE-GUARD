"""
MuleGuard Step 6 Audit Logs Verification Runner
Validates the real PostgreSQL operational and security audit operations endpoint,
RBAC enforcement, bounded pagination, server-side filtering, data sanitization,
and read-only non-mutation guarantee.
"""

import os
import sys
import json
import time
import socket
import urllib.request
import urllib.error
from http.cookiejar import CookieJar
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)

from app.db.database import get_connection
from app.db.init_auth_db import generate_deterministic_vector
from app.services.audit_service import (
    get_audit_summary,
    query_internal_audit_logs,
    sanitize_details,
    SENSITIVE_KEYS,
)

BASE_URL = "http://127.0.0.1:8000"
VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")

passed_checks = 0


def check(condition, message):
    global passed_checks
    if not condition:
        print(f"  [FAIL] {message}")
        raise AssertionError(message)
    print(f"  [OK] PASS: {message}")
    passed_checks += 1


def is_port_in_use(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


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
        # Stage 1: Password
        res1 = self.request("POST", "/api/v1/auth/stage1-login", {"employee_id": employee_id, "password": password})
        if res1["status_code"] != 200:
            raise RuntimeError(f"Login stage 1 failed: {res1}")

        ch = res1["data"]["challenge"]
        vec = generate_deterministic_vector(employee_id)
        now = time.time()
        proof = {
            "action_performed": ch["challenge_action"],
            "confidence": 0.98,
            "timestamps": [now, now + 0.5, now + 1.0]
        }

        # Stage 2: Biometric 2FA
        res2 = self.request("POST", "/api/v1/auth/stage2-verify-face", {
            "challenge_token": ch["challenge_token"],
            "probe_vector": vec,
            "liveness_proof": proof
        })
        if res2["status_code"] != 200:
            raise RuntimeError(f"Login stage 2 failed: {res2}")
        return res2["data"]


def run_unit_and_sanitization_checks():
    print("\n[Section 1] Ground-Truth PostgreSQL Audit Counters & Summary...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT (SELECT COUNT(*) FROM audit_logs) + (SELECT COUNT(*) FROM auth_audit_log);")
            db_total = cur.fetchone()[0]

    summary = get_audit_summary()
    check(isinstance(summary, dict), "Summary is a valid dict")
    check(summary["total_events"] == db_total, f"Summary total_events ({summary['total_events']}) matches real DB count ({db_total})")
    check(summary["events_today"] >= 0, "events_today is non-negative")
    check(summary["authentication_events"] >= 0, "authentication_events is non-negative")
    check(summary["security_events"] >= 0, "security_events is non-negative")
    check(summary["transaction_events"] >= 0, "transaction_events is non-negative")
    check(summary["ml_analysis_events"] >= 0, "ml_analysis_events is non-negative")

    print("\n[Section 2] Bounded Pagination Logic...")
    res_default = query_internal_audit_logs(limit=10, offset=0)
    check(res_default["status"] == "Healthy", "Status reports Healthy")
    check(res_default["retention_policy"] == "Not configured", "Retention policy reports 'Not configured'")
    check(len(res_default["items"]) <= 10, "Default query returns <= 10 items")
    check(res_default["pagination"]["limit"] == 10, "Pagination limit is 10")
    check(res_default["pagination"]["offset"] == 0, "Pagination offset is 0")
    check(res_default["pagination"]["total"] == db_total, f"Pagination total matches DB total ({db_total})")

    # Limit capped at 500
    res_large = query_internal_audit_logs(limit=9999, offset=-50)
    check(res_large["pagination"]["limit"] == 500, "Limit safely capped at 500")
    check(res_large["pagination"]["offset"] == 0, "Negative offset safely floored at 0")

    # Min limit 1
    res_min = query_internal_audit_logs(limit=-10, offset=0)
    check(res_min["pagination"]["limit"] == 1, "Limit floored at minimum 1")
    check(len(res_min["items"]) <= 1, "Returns 1 item max on limit=1")

    # Offset pagination produces distinct pages
    res_p1 = query_internal_audit_logs(limit=5, offset=0)
    res_p2 = query_internal_audit_logs(limit=5, offset=5)
    if db_total >= 10:
        check(res_p1["items"][0]["id"] != res_p2["items"][0]["id"], "Offset pagination returns consecutive distinct records")

    print("\n[Section 3] Server-Side Filtering (Category, Action, Search)...")
    res_auth = query_internal_audit_logs(limit=20, category="AUTHENTICATION")
    for it in res_auth["items"]:
        check(it["category"] == "AUTHENTICATION", f"Filtered item {it['id']} category is AUTHENTICATION")

    res_sec = query_internal_audit_logs(limit=20, category="SECURITY")
    for it in res_sec["items"]:
        check(it["category"] == "SECURITY", f"Filtered item {it['id']} category is SECURITY")

    res_search = query_internal_audit_logs(limit=10, search="LOGIN")
    check(res_search["pagination"]["total"] > 0, "Search query 'LOGIN' returns matching records")

    print("\n[Section 4] Data Sanitization & Secret Redaction...")
    dirty = {
        "password": "SecretPassword123!",
        "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$abc",
        "session_token": "live_session_token_12345",
        "probe_vector": [0.12, 0.34, 0.56],
        "user_id": "U-12345",
        "nested": {
            "token": "api_secret_jwt",
            "private_key": "-----BEGIN PRIVATE KEY-----",
            "safe_detail": "normal value"
        }
    }
    clean = sanitize_details(dirty)
    check(clean["password"] == "[REDACTED]", "Password is redacted")
    check(clean["password_hash"] == "[REDACTED]", "Password hash is redacted")
    check(clean["session_token"] == "[REDACTED]", "Session token is redacted")
    check(clean["probe_vector"] == "[REDACTED]", "Probe vector is redacted")
    check(clean["nested"]["token"] == "[REDACTED]", "Nested token is redacted")
    check(clean["nested"]["private_key"] == "[REDACTED]", "Nested private key is redacted")
    check(clean["nested"]["safe_detail"] == "normal value", "Safe fields preserved unchanged")

    # Check live items returned from PostgreSQL
    for it in res_default["items"]:
        d_str = json.dumps(it.get("details", {})).lower()
        for sk in ["password_hash", "private_key", "session_token"]:
            if sk in d_str:
                check("[redacted]" in d_str, f"Sensitive key '{sk}' in item {it['id']} is redacted")

    print("\n[Section 5] Non-Mutation Verification...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT (SELECT COUNT(*) FROM audit_logs) + (SELECT COUNT(*) FROM auth_audit_log);")
            cnt_before = cur.fetchone()[0]

    # Run queries, summary, filters
    _ = get_audit_summary()
    _ = query_internal_audit_logs(limit=50, offset=0)
    _ = query_internal_audit_logs(limit=50, offset=50)
    _ = query_internal_audit_logs(limit=10, category="SECURITY")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT (SELECT COUNT(*) FROM audit_logs) + (SELECT COUNT(*) FROM auth_audit_log);")
            cnt_after = cur.fetchone()[0]

    check(cnt_before == cnt_after, f"Non-mutation holds: DB count before ({cnt_before}) == DB count after ({cnt_after})")


def run_http_endpoint_tests():
    server_process = None
    started_by_test = False

    if not is_port_in_use(8000):
        print("\n[Setup] Starting live FastAPI server on port 8000...")
        server_process = subprocess.Popen(
            [VENV_PYTHON, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1"],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        started_by_test = True
        for _ in range(30):
            if is_port_in_use(8000):
                print("[Setup] Server listening on port 8000.")
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Test server failed to start on port 8000.")
    else:
        print("\n[Setup] Using existing server process on port 8000.")

    try:
        anon_client = AuthenticatedClient()

        print("\n[Section 6] Unauthenticated Requests Return 401...")
        res_anon = anon_client.request("GET", "/api/v1/internal/audit-logs")
        check(res_anon["status_code"] == 401, f"Unauthenticated /audit-logs returns 401 Unauthorized (got {res_anon['status_code']})")

        print("\n[Section 7] Investigator Role Rejection (403 Forbidden)...")
        inv_client = AuthenticatedClient()
        inv_client.login("MG-INV-001")  # Investigator
        res_inv = inv_client.request("GET", "/api/v1/internal/audit-logs")
        check(res_inv["status_code"] == 403, f"Investigator forbidden from /audit-logs (got {res_inv['status_code']})")

        print("\n[Section 8] Compliance Role Rejection (403 Forbidden)...")
        comp_client = AuthenticatedClient()
        comp_client.login("MG-CMP-001")  # Compliance
        res_comp = comp_client.request("GET", "/api/v1/internal/audit-logs")
        check(res_comp["status_code"] == 403, f"Compliance forbidden from /audit-logs (got {res_comp['status_code']})")

        print("\n[Section 9] Internal Team Access Allowed (200 OK)...")
        admin_client = AuthenticatedClient()
        admin_client.login("MG-ADM-001")  # Internal Team / Admin
        res_admin = admin_client.request("GET", "/api/v1/internal/audit-logs?limit=10&offset=0")
        check(res_admin["status_code"] == 200, f"Internal Team / Admin can access /audit-logs (got {res_admin['status_code']})")

        data = res_admin["data"]
        check(data["status"] == "Healthy", f"Endpoint reports Healthy status (got {data['status']})")
        check(data["retention_policy"] == "Not configured", "Endpoint reports 'Retention policy: Not configured'")
        check("summary" in data, "Response includes summary metrics")
        check("pagination" in data, "Response includes pagination block")
        check("items" in data, "Response includes items array")
        check(len(data["items"]) <= 10, f"Limit applied: received {len(data['items'])} items")

        print("\n[Section 10] Server-Side HTTP Query Parameters...")
        res_filtered = admin_client.request("GET", "/api/v1/internal/audit-logs?category=AUTHENTICATION&limit=5")
        check(res_filtered["status_code"] == 200, "GET with category filter returns 200")
        for item in res_filtered["data"]["items"]:
            check(item["category"] == "AUTHENTICATION", "Item category correctly filtered over HTTP")

        res_search = admin_client.request("GET", "/api/v1/internal/audit-logs?search=STAGE1&limit=5")
        check(res_search["status_code"] == 200, "GET with search filter returns 200")
        check(len(res_search["data"]["items"]) > 0, "Search query returned matching items over HTTP")

    finally:
        if started_by_test and server_process:
            print("\n[Teardown] Terminating test server process...")
            server_process.terminate()
            server_process.wait(timeout=5)
            print("[Teardown] Server stopped.")


def run_frontend_assets_checks():
    print("\n[Section 11] Frontend Assets Verification...")
    api_js_path = os.path.join(PROJECT_DIR, "frontend", "scripts", "api.js")
    with open(api_js_path, "r", encoding="utf-8") as f:
        api_code = f.read()
    check("getInternalAuditLogs" in api_code, "api.js implements getInternalAuditLogs")

    dash_path = os.path.join(PROJECT_DIR, "frontend", "internal", "dashboard.html")
    with open(dash_path, "r", encoding="utf-8") as f:
        dash_code = f.read()

    required_elements = [
        "section-logs",
        "logs-summary-total",
        "logs-summary-today",
        "logs-summary-auth",
        "logs-summary-sec",
        "logs-summary-tx",
        "logs-summary-ml",
        "logs-filter-category",
        "logs-filter-search",
        "logs-filter-action",
        "logs-filter-limit",
        "audit-logs-tbody",
        "logs-btn-prev",
        "logs-btn-next",
        "audit-detail-modal",
        "startLogsPolling",
        "stopLogsPolling",
        "renderLogsTab",
    ]
    for el in required_elements:
        check(el in dash_code, f"dashboard.html contains {el}")


def main():
    print("=" * 60)
    print("MULEGUARD AUDIT LOGS OPERATIONS & TELEMETRY VERIFICATION")
    print("=" * 60)

    run_unit_and_sanitization_checks()
    run_http_endpoint_tests()
    run_frontend_assets_checks()

    print("\n" + "=" * 60)
    print(f"ALL AUDIT LOG CHECKS PASSED: {passed_checks}/{passed_checks} PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
