"""
MuleGuard Step 2: Compliance Audit Trail Verification Runner
Tests:
1. Unauthenticated access blocked (401)
2. Investigator access blocked (403)
3. Compliance officer access allowed (200)
4. Internal team access allowed (200)
5. Summary KPI endpoint (/api/v1/audit-logs/summary) returns real PostgreSQL counts
6. Bounded pagination & envelope format (/api/v1/audit-logs?format=envelope)
7. Server-side category filtering & search
8. Data sanitization & secret redaction
9. HTML file and DOM elements integrity
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)

from app.db.database import get_connection
from app.db.init_auth_db import generate_deterministic_vector
from app.services.audit_service import get_audit_summary, SENSITIVE_KEYS

BASE_URL = "http://127.0.0.1:8000"

passed_checks = 0


def check(condition, message):
    global passed_checks
    if not condition:
        print(f"  [FAIL] {message}")
        raise AssertionError(message)
    print(f"  [OK] PASS: {message}")
    passed_checks += 1


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
                    "headers": dict(resp.headers),
                    "data": json.loads(resp_body) if resp_body else {},
                    "cookies": {c.name: c.value for c in self.cookie_jar}
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            return {
                "status_code": e.code,
                "headers": dict(e.headers),
                "data": json.loads(err_body) if err_body.startswith("{") else {"detail": err_body},
                "cookies": {c.name: c.value for c in self.cookie_jar}
            }

    def login(self, employee_id, password="Password@123"):
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

        res2 = self.request("POST", "/api/v1/auth/stage2-verify-face", {
            "challenge_token": ch["challenge_token"],
            "probe_vector": vec,
            "liveness_proof": proof
        })
        if res2["status_code"] != 200:
            raise RuntimeError(f"Login stage 2 failed: {res2}")
        return self


def main():
    print("=" * 65)
    print("MULEGUARD COMPLIANCE AUDIT TRAIL VERIFICATION SUITE")
    print("=" * 65)

    # 1. Unauthenticated Blocked
    print("\n[Check 1] Unauthenticated Access Protection...")
    anon = AuthenticatedClient()
    res_anon = anon.request("GET", "/api/v1/audit-logs")
    check(res_anon["status_code"] == 401, f"Unauthenticated access returns 401 Unauthorized (got {res_anon['status_code']})")
    res_anon_sum = anon.request("GET", "/api/v1/audit-logs/summary")
    check(res_anon_sum["status_code"] == 401, f"Unauthenticated summary returns 401 Unauthorized (got {res_anon_sum['status_code']})")

    # 2. Investigator Blocked
    print("\n[Check 2] Investigator Access Blocked (RBAC)...")
    inv = AuthenticatedClient().login("MG-INV-001")
    res_inv = inv.request("GET", "/api/v1/audit-logs")
    check(res_inv["status_code"] == 403, f"Investigator access returns 403 Forbidden (got {res_inv['status_code']})")
    res_inv_sum = inv.request("GET", "/api/v1/audit-logs/summary")
    check(res_inv_sum["status_code"] == 403, f"Investigator summary returns 403 Forbidden (got {res_inv_sum['status_code']})")

    # 3. Compliance Officer Allowed
    print("\n[Check 3] Compliance Officer Access Allowed (RBAC)...")
    comp = AuthenticatedClient().login("MG-CMP-001")
    res_comp = comp.request("GET", "/api/v1/audit-logs?limit=10")
    check(res_comp["status_code"] == 200, f"Compliance access returns 200 OK (got {res_comp['status_code']})")
    check(isinstance(res_comp["data"], list), "Default format returns list of items")
    check(len(res_comp["data"]) <= 10, f"Limit 10 respected: got {len(res_comp['data'])} items")

    # 4. Internal Team Access Preserved
    print("\n[Check 4] Internal Team Access Preserved...")
    admin = AuthenticatedClient().login("MG-ADM-001")
    res_adm = admin.request("GET", "/api/v1/audit-logs?limit=5")
    check(res_adm["status_code"] == 200, f"Admin access returns 200 OK (got {res_adm['status_code']})")
    check(isinstance(res_adm["data"], list), "Admin default format returns list")

    # 5. Live Summary Counts Match Database
    print("\n[Check 5] Live Audit Summary Direct Matching...")
    res_sum = comp.request("GET", "/api/v1/audit-logs/summary")
    check(res_sum["status_code"] == 200, f"Compliance summary returns 200 OK (got {res_sum['status_code']})")
    sum_data = res_sum["data"]

    db_summary = get_audit_summary()
    check(sum_data["total_events"] == db_summary["total_events"], f"total_events ({sum_data['total_events']}) matches real PostgreSQL count ({db_summary['total_events']})")
    check(sum_data["authentication_events"] == db_summary["authentication_events"], f"authentication_events ({sum_data['authentication_events']}) matches DB count")
    check(sum_data["security_events"] == db_summary["security_events"], f"security_events ({sum_data['security_events']}) matches DB count")
    check(sum_data["transaction_events"] == db_summary["transaction_events"], f"transaction_events ({sum_data['transaction_events']}) matches DB count")

    # 6. Envelope Format & Pagination
    print("\n[Check 6] Envelope Format & Pagination...")
    res_env = comp.request("GET", "/api/v1/audit-logs?limit=15&offset=0&format=envelope")
    check(res_env["status_code"] == 200, "Envelope request returns 200 OK")
    env_data = res_env["data"]
    check("items" in env_data, "Envelope contains 'items'")
    check("pagination" in env_data, "Envelope contains 'pagination'")
    check("summary" in env_data, "Envelope contains 'summary'")
    check(len(env_data["items"]) <= 15, f"Envelope items count ({len(env_data['items'])}) <= limit (15)")
    check(env_data["pagination"]["limit"] == 15, "Pagination limit is 15")
    check(env_data["pagination"]["offset"] == 0, "Pagination offset is 0")
    check(env_data["pagination"]["total"] == db_summary["total_events"], "Pagination total matches database count")

    # Offset pagination produces distinct pages
    res_p1 = comp.request("GET", "/api/v1/audit-logs?limit=5&offset=0&format=envelope")
    res_p2 = comp.request("GET", "/api/v1/audit-logs?limit=5&offset=5&format=envelope")
    if db_summary["total_events"] >= 10:
        check(res_p1["data"]["items"][0]["id"] != res_p2["data"]["items"][0]["id"], "Consecutive pages return distinct records")

    # 7. Category and Search Filtering
    print("\n[Check 7] Category & Search Filtering...")
    res_auth = comp.request("GET", "/api/v1/audit-logs?category=AUTHENTICATION&limit=10&format=envelope")
    check(res_auth["status_code"] == 200, "Category AUTHENTICATION query returns 200")
    for it in res_auth["data"]["items"]:
        check(it["category"] == "AUTHENTICATION", f"Item {it['id']} has category AUTHENTICATION")

    res_sec = comp.request("GET", "/api/v1/audit-logs?category=SECURITY&limit=10&format=envelope")
    check(res_sec["status_code"] == 200, "Category SECURITY query returns 200")
    for it in res_sec["data"]["items"]:
        check(it["category"] == "SECURITY", f"Item {it['id']} has category SECURITY")

    res_search = comp.request("GET", "/api/v1/audit-logs?search=LOGIN&limit=5&format=envelope")
    check(res_search["status_code"] == 200, "Search query returns 200")
    check(len(res_search["data"]["items"]) > 0, "Search 'LOGIN' returns matching items")

    # 8. Secret Redaction & Sanitization
    print("\n[Check 8] Secret Redaction & Data Sanitization...")
    res_all = comp.request("GET", "/api/v1/audit-logs?limit=100&format=envelope")
    for it in res_all["data"]["items"]:
        d_str = json.dumps(it.get("details", {})).lower()
        for sk in ["password_hash", "private_key", "session_token", "probe_vector"]:
            if sk in d_str:
                check("[redacted]" in d_str, f"Sensitive key '{sk}' in item {it['id']} is redacted")

    # 9. Frontend Production HTML Integrity
    print("\n[Check 9] Frontend audit-trail.html Structure & Security...")
    html_path = os.path.join(PROJECT_DIR, "frontend", "bank", "compliance", "audit-trail.html")
    check(os.path.exists(html_path), "frontend/bank/compliance/audit-trail.html exists")

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Check required UI elements
    required_ids = [
        "sidebar-container",
        "kpi-total-events",
        "kpi-auth-events",
        "kpi-sec-events",
        "kpi-tx-events",
        "audit-badge-total",
        "filter-search",
        "filter-category",
        "filter-limit",
        "btn-refresh",
        "audit-table-body",
        "audit-pagination-info",
        "audit-page-number",
        "btn-prev",
        "btn-next",
        "audit-detail-modal",
        "modal-event-id",
        "modal-category-badge",
        "modal-action-text",
        "modal-actor-text",
        "modal-result-badge",
        "modal-timestamp-text",
        "modal-resource-text",
        "modal-ip-text",
        "modal-details-payload"
    ]
    for rid in required_ids:
        check(f'id="{rid}"' in html_content, f"audit-trail.html contains element #{rid}")

    # Verify no MuleGuardStore calls
    check("MuleGuardStore" not in html_content, "Zero MuleGuardStore calls in audit-trail.html")
    check("MuleGuardAPI.getAuditLogs" in html_content, "Uses MuleGuardAPI.getAuditLogs")
    check("MuleGuardAPI.getAuditSummary" in html_content, "Uses MuleGuardAPI.getAuditSummary")

    print("\n" + "=" * 65)
    print(f"ALL COMPLIANCE AUDIT TRAIL CHECKS PASSED: {passed_checks}/{passed_checks} PASS")
    print("=" * 65)


if __name__ == "__main__":
    main()
