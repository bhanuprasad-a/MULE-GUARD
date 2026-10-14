"""
Verify Step 9I Live HTTP Endpoints for Dashboards and Reports
Tests authentication, authorization, and data retrieval for all endpoints
used by the migrated dashboards and reports.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)

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
    print("=== STEP 9I: LIVE HTTP ENDPOINT VERIFICATION ===")
    
    # 1. Bank Compliance Session
    print("\n1. Testing Compliance Dashboard Endpoints (Role: bank_compliance - MG-CMP-001)...")
    comp = AuthenticatedClient().login("MG-CMP-001")
    
    res = comp.request("GET", "/api/v1/kpis")
    assert res["status_code"] == 200, f"KPIs failed: {res}"
    print(f"  [PASS] Compliance KPIs -> Status: {res['status_code']}, Accounts: {res['data'].get('total_accounts')}, Cases: {res['data'].get('active_cases')}, Alerts: {res['data'].get('open_alerts')}")
    
    res = comp.request("GET", "/api/v1/cases?limit=10")
    assert res["status_code"] == 200, f"Cases failed: {res}"
    print(f"  [PASS] Cases list -> Status: {res['status_code']}, Count: {len(res['data'])}")
    
    res = comp.request("GET", "/api/v1/alerts?limit=10")
    assert res["status_code"] == 200, f"Alerts failed: {res}"
    print(f"  [PASS] Alerts list -> Status: {res['status_code']}, Count: {len(res['data'])}")
    
    res = comp.request("GET", "/api/v1/decisions?limit=10")
    assert res["status_code"] == 200, f"Decisions failed: {res}"
    print(f"  [PASS] Decisions list -> Status: {res['status_code']}, Count: {len(res['data'])}")
    
    res = comp.request("GET", "/api/v1/audit-logs?limit=10")
    assert res["status_code"] == 200, f"Audit logs failed: {res}"
    print(f"  [PASS] Compliance Audit Logs -> Status: {res['status_code']}, Count: {len(res['data'])}")

    # 2. Bank Investigator Session
    print("\n2. Testing Investigator Dashboard Endpoints (Role: bank_investigator - MG-INV-001)...")
    inv = AuthenticatedClient().login("MG-INV-001")
    
    res = inv.request("GET", "/api/v1/kpis")
    assert res["status_code"] == 200, f"Investigator KPIs failed: {res}"
    print(f"  [PASS] Investigator KPIs -> Status: {res['status_code']}, Total Txs: {res['data'].get('total_transactions')}")
    
    res = inv.request("GET", "/api/v1/transactions?limit=10")
    assert res["status_code"] == 200, f"Transactions failed: {res}"
    print(f"  [PASS] Transactions list -> Status: {res['status_code']}, Count: {len(res['data'])}")
    
    res = inv.request("GET", "/api/v1/accounts?limit=10")
    assert res["status_code"] == 200, f"Accounts failed: {res}"
    print(f"  [PASS] Accounts list -> Status: {res['status_code']}, Count: {len(res['data'])}")
    
    res = inv.request("GET", "/api/v1/cases?limit=1")
    if len(res["data"]) > 0:
        c_id = res["data"][0].get("case_id") or res["data"][0].get("id")
        res_case = inv.request("GET", f"/api/v1/cases/{c_id}")
        assert res_case["status_code"] == 200, f"Case detail failed: {res_case}"
        print(f"  [PASS] Single Case detail -> Status: {res_case['status_code']}, Entity: {res_case['data'].get('entity') or res_case['data'].get('title')}")

    print("\n>>> ALL STEP 9I DASHBOARD & REPORT LIVE API ENDPOINTS VERIFIED 100% PASS <<<")


if __name__ == "__main__":
    main()
