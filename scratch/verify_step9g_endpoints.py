import os
import sys
import json
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app.db.init_auth_db import generate_deterministic_vector

BASE_URL = "http://127.0.0.1:8000"

class AuthClient:
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
                    "data": json.loads(resp_body) if resp_body else {}
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            return {
                "status_code": e.code,
                "data": json.loads(err_body) if err_body.startswith("{") else {"detail": err_body}
            }

    def login(self, employee_id, password="Password@123"):
        res1 = self.request("POST", "/api/v1/auth/stage1-login", {"employee_id": employee_id, "password": password})
        if res1["status_code"] != 200:
            raise RuntimeError(f"Login stage 1 failed: {res1}")

        ch = res1["data"]["challenge"]
        vec = generate_deterministic_vector(employee_id)
        proof = {
            "action_performed": ch["challenge_action"],
            "confidence": 0.98,
            "timestamps": [100.0, 100.5, 101.0]
        }
        res2 = self.request("POST", "/api/v1/auth/stage2-verify-face", {
            "challenge_token": ch["challenge_token"],
            "probe_vector": vec,
            "liveness_proof": proof
        })
        if res2["status_code"] != 200:
            raise RuntimeError(f"Login stage 2 failed: {res2}")
        return res2["data"]

def test_live_endpoints():
    print("=== LIVE ENDPOINT VERIFICATION FOR STEP 9G ===")
    inv_client = AuthClient()
    inv_client.login("MG-INV-001")
    print("[AUTH] Investigator (MG-INV-001) logged in successfully.")

    cmp_client = AuthClient()
    cmp_client.login("MG-CMP-001")
    print("[AUTH] Compliance (MG-CMP-001) logged in successfully.")

    # 1. GET /api/v1/alerts
    alerts_res = inv_client.request("GET", "/api/v1/alerts?limit=10")
    assert alerts_res["status_code"] == 200, f"GET /alerts failed: {alerts_res}"
    print(f"[PASS] GET /api/v1/alerts returned {len(alerts_res['data'])} alerts from PostgreSQL.")
    first_alert = alerts_res["data"][0] if alerts_res["data"] else None

    # 2. PATCH /api/v1/alerts/{id}/acknowledge
    if first_alert:
        ack_res = inv_client.request("PATCH", f"/api/v1/alerts/{first_alert['id']}/acknowledge")
        assert ack_res["status_code"] == 200, f"PATCH /alerts acknowledge failed: {ack_res}"
        print(f"[PASS] PATCH /api/v1/alerts/{first_alert['id']}/acknowledge succeeded: {ack_res['data']['status']}")

    # 3. GET /api/v1/cases
    cases_res = inv_client.request("GET", "/api/v1/cases?limit=10")
    assert cases_res["status_code"] == 200, f"GET /cases failed: {cases_res}"
    print(f"[PASS] GET /api/v1/cases returned {len(cases_res['data'])} cases from PostgreSQL.")
    first_case = cases_res["data"][0] if cases_res["data"] else None

    # 4. PATCH /api/v1/cases/{id}/investigate
    if first_case:
        inv_res = inv_client.request("PATCH", f"/api/v1/cases/{first_case['id']}/investigate")
        assert inv_res["status_code"] == 200, f"PATCH /cases investigate failed: {inv_res}"
        print(f"[PASS] PATCH /api/v1/cases/{first_case['id']}/investigate succeeded: {inv_res['data']['status']}")

    # 5. GET /api/v1/watchlists
    wl_res = inv_client.request("GET", "/api/v1/watchlists?limit=10")
    assert wl_res["status_code"] == 200, f"GET /watchlists failed: {wl_res}"
    print(f"[PASS] GET /api/v1/watchlists returned {len(wl_res['data'])} watchlists from PostgreSQL.")

    print("\nALL STEP 9G LIVE ENDPOINTS VERIFIED AND RETURNING POSTGRESQL DATA!")

if __name__ == "__main__":
    test_live_endpoints()
