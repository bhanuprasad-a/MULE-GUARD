"""
verify_compliance_watchlists.py
Comprehensive verification script for Compliance Watchlist page, backend API, audit trail logging, and security controls.
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

BASE_URL = "http://127.0.0.1:8000"

passed_checks = 0
failed_checks = 0

def check(condition, message):
    global passed_checks, failed_checks
    if not condition:
        print(f"  [FAIL] {message}")
        failed_checks += 1
    else:
        print(f"  [PASS] {message}")
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
            try:
                err_data = json.loads(err_body)
            except Exception:
                err_data = {"detail": err_body}
            return {
                "status_code": e.code,
                "headers": dict(e.headers),
                "data": err_data,
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
    print("MULEGUARD COMPLIANCE WATCHLIST VERIFICATION SUITE")
    print("=" * 65)

    # 1. Unauthenticated Request Blocked
    print("\n[Check 1] Unauthenticated Access Protection...")
    anon = AuthenticatedClient()
    res_anon = anon.request("GET", "/api/v1/watchlists")
    check(res_anon["status_code"] == 401, f"Unauthenticated access returns 401 Unauthorized (got {res_anon['status_code']})")

    # 2. Compliance Officer Access Allowed
    print("\n[Check 2] Compliance Officer Access Allowed (RBAC)...")
    comp = AuthenticatedClient().login("MG-CMP-001")
    res_comp = comp.request("GET", "/api/v1/watchlists")
    check(res_comp["status_code"] == 200, f"Compliance access returns 200 OK (got {res_comp['status_code']})")
    check(isinstance(res_comp["data"], list), "Watchlists returns a list from PostgreSQL")
    print(f"      Total existing watchlist entries: {len(res_comp['data'])}")

    # 3. Investigator & Admin Access Preserved
    print("\n[Check 3] Investigator & Admin Access Preserved...")
    inv = AuthenticatedClient().login("MG-INV-001")
    res_inv = inv.request("GET", "/api/v1/watchlists")
    check(res_inv["status_code"] == 200, f"Investigator access returns 200 OK (got {res_inv['status_code']})")

    admin = AuthenticatedClient().login("MG-ADM-001")
    res_adm = admin.request("GET", "/api/v1/watchlists")
    check(res_adm["status_code"] == 200, f"Admin access returns 200 OK (got {res_adm['status_code']})")

    # 4. Server-Side Filtering (Search and Status)
    print("\n[Check 4] Server-Side Filtering (search & status parameters)...")
    res_active = comp.request("GET", "/api/v1/watchlists?status=active")
    check(res_active["status_code"] == 200, "Filter by status=active returns 200 OK")
    if len(res_active["data"]) > 0:
        all_active = all(w.get("status") == "active" for w in res_active["data"])
        check(all_active, "All returned records have status == 'active'")

    # 5. Add to Watchlist & PostgreSQL Audit Trail Logging
    print("\n[Check 5] Add to Watchlist & PostgreSQL Audit Trail Verification...")
    res_accounts = comp.request("GET", "/api/v1/accounts?limit=100")
    check(res_accounts["status_code"] == 200, "GET /api/v1/accounts returns 200 OK")

    accounts_list = res_accounts["data"]
    if isinstance(accounts_list, dict) and "items" in accounts_list:
        accounts_list = accounts_list["items"]

    current_watchlists = res_comp["data"]
    existing_watch_ids = {w.get("account_id") for w in current_watchlists}

    target_acc_id = None
    if isinstance(accounts_list, list):
        for acc in accounts_list:
            aid = acc.get("account_id")
            if aid and aid not in existing_watch_ids:
                target_acc_id = aid
                break

    if not target_acc_id and len(current_watchlists) > 0:
        target_acc_id = current_watchlists[0].get("account_id")

    check(target_acc_id is not None, f"Target account identified: {target_acc_id}")

    test_reason = "Mandatory regulatory review - suspicious transaction frequency pattern"
    res_add = comp.request("POST", f"/api/v1/watchlists/{target_acc_id}", {
        "reason": test_reason,
        "priority": "high"
    })
    check(res_add["status_code"] == 200, f"POST /api/v1/watchlists/{target_acc_id} returns 200 OK")

    # Verify directly against PostgreSQL database
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check watchlist record
            cur.execute("SELECT account_id, reason, status FROM watchlists WHERE account_id = %s", (target_acc_id,))
            w_rows = cur.fetchall()
            w_row = w_rows[-1] if w_rows else None
            check(w_row is not None and w_row[1] == test_reason, "Watchlist record correctly persisted in PostgreSQL watchlists table")

            # Check audit log record
            cur.execute(
                "SELECT action, entity_type, entity_id, account_id, details FROM audit_logs WHERE entity_type = 'watchlist' AND account_id = %s ORDER BY created_at DESC LIMIT 1",
                (target_acc_id,)
            )
            audit_row = cur.fetchone()
            check(audit_row is not None and audit_row[0] == "WATCHLIST_ADDED", "PostgreSQL audit_logs records action='WATCHLIST_ADDED'")
            if audit_row:
                details = audit_row[4]
                if isinstance(details, str):
                    details = json.loads(details)
                check(details.get("reason") == test_reason, "Audit log details JSON contains accurate watchlist reason")
                check("actor" in details, f"Audit log details records actor: {details.get('actor')}")

    # 6. Verify Static / Frontend Policy Compliance
    print("\n[Check 6] Frontend Page Structural & Policy Conformance...")
    page_path = os.path.join(PROJECT_DIR, "frontend", "bank", "compliance", "watchlists.html")
    check(os.path.isfile(page_path), "frontend/bank/compliance/watchlists.html exists")

    with open(page_path, "r", encoding="utf-8") as f:
        html = f.read()

    check("scripts/auth-guard.js" in html, "Includes auth-guard.js for institutional RBAC enforcement")
    check("scripts/api.js" in html, "Includes api.js for PostgreSQL backend communication")
    check("MuleGuardStore" not in html, "Zero MuleGuardStore references (strictly avoids local mock state)")
    check("localStorage.getItem('muleguard_accounts')" not in html, "Zero localStorage banking data reads")
    check('id="btn-remove-watchlist"' not in html and "deleteWatchlist" not in html, "No fake delete/removal buttons (honors statutory non-removal constraint)")
    check("Statutory" in html, "Explicit statutory retention policy notice present in UI")

    # Check Required KPI elements
    check('id="kpi-total-watchlisted"' in html, "Live KPI: kpi-total-watchlisted present")
    check('id="kpi-active-watchlisted"' in html, "Live KPI: kpi-active-watchlisted present")
    check('id="kpi-high-priority"' in html, "Live KPI: kpi-high-priority present")
    check('id="kpi-total-exposure"' in html, "Live KPI: kpi-total-exposure present")

    # Check Required Table & Interaction elements
    check('id="watchlist-table-body"' in html, "Watchlist table: watchlist-table-body present")
    check('id="filter-search"' in html, "Search input: filter-search present")
    check('id="filter-priority"' in html, "Priority filter: filter-priority present")
    check('id="filter-status"' in html, "Status filter: filter-status present")
    check('id="account-detail-modal"' in html, "Account inspect modal: account-detail-modal present")
    check('id="add-watchlist-modal"' in html, "Add to watchlist modal: add-watchlist-modal present")
    check('id="select-account-id"' in html, "Account select dropdown: select-account-id present")
    check('id="input-watchlist-reason"' in html, "Reason input with validation: input-watchlist-reason present")

    print("\n" + "=" * 65)
    if failed_checks == 0:
        print(f"ALL TESTS PASSED: {passed_checks}/{passed_checks}")
        print("=" * 65)
        return 0
    else:
        print(f"SOME TESTS FAILED: {passed_checks} passed, {failed_checks} failed")
        print("=" * 65)
        return 1

if __name__ == "__main__":
    sys.exit(main())
