import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
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

def test_decisions_endpoints():
    print("====================================================")
    print("MULEGUARD STEP 9H DECISIONS API LIVE VERIFICATION")
    print("====================================================")

    # 1. Unauthenticated access
    unauth = AuthClient()
    unauth_res = unauth.request("GET", "/api/v1/decisions")
    assert unauth_res["status_code"] == 401, f"Expected 401 for unauthenticated, got {unauth_res['status_code']}"
    print("[PASS] Unauthenticated request to /api/v1/decisions correctly returned 401 Unauthorized.")

    # 2. Investigator access (should be 403 Forbidden since decisions are bank_compliance only)
    inv = AuthClient()
    inv.login("MG-INV-001")
    inv_res = inv.request("GET", "/api/v1/decisions")
    assert inv_res["status_code"] == 403, f"Expected 403 for investigator, got {inv_res['status_code']}"
    print("[PASS] Investigator request to /api/v1/decisions correctly returned 403 Forbidden.")

    # 3. Compliance access (should be 200 OK)
    cmp_client = AuthClient()
    cmp_client.login("MG-CMP-001")
    cmp_res = cmp_client.request("GET", "/api/v1/decisions?limit=50")
    assert cmp_res["status_code"] == 200, f"Expected 200 for compliance, got {cmp_res}"
    initial_decisions = cmp_res["data"]
    assert isinstance(initial_decisions, list), "Expected list of decisions"
    print(f"[PASS] Compliance officer request to GET /api/v1/decisions returned 200 OK with {len(initial_decisions)} records.")

    # 4. Create decision (POST /api/v1/decisions/{account_id})
    # Fetch real alert to satisfy foreign key constraint if alert_id is provided
    alerts_res = cmp_client.request("GET", "/api/v1/alerts?limit=1")
    real_alert_id = alerts_res["data"][0]["id"] if alerts_res["status_code"] == 200 and alerts_res["data"] else None

    target_account = "ACC-982001"
    q_params_dict = {
        "decision": "Block",
        "reason": "Automated test compliance block decision"
    }
    if real_alert_id:
        q_params_dict["alert_id"] = real_alert_id

    q_params = urllib.parse.urlencode(q_params_dict)
    post_res = cmp_client.request("POST", f"/api/v1/decisions/{target_account}?{q_params}")
    assert post_res["status_code"] == 200, f"Expected 200 for POST /decisions, got {post_res}"
    new_dec = post_res["data"]
    assert new_dec["account_id"] == target_account
    assert new_dec["decision"] == "Block"
    print(f"[PASS] POST /api/v1/decisions/{target_account} succeeded: created {new_dec['id']} (decision={new_dec['decision']}, alert_id={new_dec.get('alert_id')}).")

    # 5. Invalid decision validation (must be one of Monitor, Clear, Block, Escalate)
    invalid_q = urllib.parse.urlencode({"decision": "InvalidAction"})
    bad_res = cmp_client.request("POST", f"/api/v1/decisions/{target_account}?{invalid_q}")
    assert bad_res["status_code"] == 400, f"Expected 400 for invalid decision, got {bad_res}"
    print("[PASS] POST /api/v1/decisions with invalid decision rejected with 400 Bad Request.")

    # 6. Verify newly created decision in list
    verify_res = cmp_client.request("GET", "/api/v1/decisions?limit=50")
    assert verify_res["status_code"] == 200
    ids = [d["id"] for d in verify_res["data"]]
    assert new_dec["id"] in ids, f"Created decision {new_dec['id']} not found in GET /decisions list"
    print(f"[PASS] Verified new decision {new_dec['id']} persisted in PostgreSQL and returned via GET /api/v1/decisions.")

    print("\nALL DECISION API LIVE VERIFICATION CHECKS PASSED: 6/6 PASS")

if __name__ == "__main__":
    test_decisions_endpoints()
