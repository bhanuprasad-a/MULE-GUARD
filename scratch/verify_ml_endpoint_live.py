"""
MuleGuard Live Endpoint & RBAC Verification for /api/v1/internal/ml-health
Tests:
1. Server Startup / Health Check
2. Unauthenticated request to /api/v1/internal/ml-health -> 401 Unauthorized
3. Investigator persona (MG-INV-001) -> 403 Forbidden
4. Compliance persona (MG-CMP-001) -> 403 Forbidden
5. Internal Team / Admin persona (MG-ADM-001) -> 200 OK with full ML telemetry payload
6. End-to-end Inference Telemetry Update:
   - Investigator triggers an account risk analysis (/api/v1/alerts/analyze/ACC-982001)
   - Internal Team queries /api/v1/internal/ml-health
   - Verifies total_inferences incremented, latency tracked, risk distribution updated
"""

import os
import sys
import time
import json
import socket
import subprocess
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app.db.init_auth_db import generate_deterministic_vector

BASE_URL = "http://127.0.0.1:8000"
VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")


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


def run_live_tests():
    print("====================================================")
    print("MULEGUARD ML HEALTH LIVE ENDPOINT & RBAC TEST")
    print("====================================================")

    server_process = None
    if not is_port_in_use(8000):
        print("[Setup] Starting live FastAPI server on port 8000...")
        server_process = subprocess.Popen(
            [VENV_PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Wait up to 10 seconds for port to open
        for _ in range(20):
            time.sleep(0.5)
            if is_port_in_use(8000):
                print("[Setup] Server listening on port 8000.")
                break
        else:
            raise RuntimeError("Server failed to start on port 8000.")

    passed_tests = 0
    total_tests = 0

    def assert_test(cond, title):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if cond:
            passed_tests += 1
            print(f"  [OK] PASS: {title}")
        else:
            print(f"  [FAIL] FAIL: {title}")
            assert False, title

    try:
        # 1. Unauthenticated Request
        print("\n[Section 1] Unauthenticated Requests Return 401...")
        anon = AuthenticatedClient()
        res = anon.request("GET", "/api/v1/internal/ml-health")
        assert_test(res["status_code"] == 401, "Unauthenticated /ml-health returns 401 Unauthorized")

        # 2. Investigator Request (Should be 403 Forbidden)
        print("\n[Section 2] Investigator Role Rejection (403 Forbidden)...")
        inv = AuthenticatedClient()
        inv.login("MG-INV-001")
        res = inv.request("GET", "/api/v1/internal/ml-health")
        assert_test(res["status_code"] == 403, "Investigator forbidden from /ml-health (403 Forbidden)")

        # 3. Compliance Request (Should be 403 Forbidden)
        print("\n[Section 3] Compliance Role Rejection (403 Forbidden)...")
        cmp_user = AuthenticatedClient()
        cmp_user.login("MG-CMP-001")
        res = cmp_user.request("GET", "/api/v1/internal/ml-health")
        assert_test(res["status_code"] == 403, "Compliance forbidden from /ml-health (403 Forbidden)")

        # 4. Internal Team / Admin Request (Should be 200 OK)
        print("\n[Section 4] Internal Team Access Allowed (200 OK)...")
        adm = AuthenticatedClient()
        adm.login("MG-ADM-001")
        res = adm.request("GET", "/api/v1/internal/ml-health")
        assert_test(res["status_code"] == 200, "Internal Team / Admin can access /ml-health (200 OK)")

        data = res["data"]
        assert_test(data["status"] == "Healthy", "ML status is Healthy")
        assert_test(data["model"]["name"] == "muleguard_postgres_model.json", "Active model name is muleguard_postgres_model.json")
        assert_test(data["model"]["trees_count"] == 80, "Trees count is 80")
        assert_test(data["model"]["features_count"] == 26, "Feature count is 26")
        assert_test(data["model"]["features_compatible"] is True, "Features compatible is True")
        assert_test(data["features_health"]["status"] == "Valid", "Feature health status is Valid")
        assert_test(len(data["model"]["all_features"]) == 26, "All 26 features present in model schema")
        assert_test(data["thresholds"]["decision_threshold"] == 0.50, "Decision threshold is 0.50")

        # 5. Live Inference Telemetry End-to-End Test
        print("\n[Section 5] Live End-to-End Inference Telemetry Verification...")
        initial_inferences = data["telemetry"]["total_inferences"]

        # Trigger risk analysis via investigator endpoint
        analyze_res = inv.request("POST", "/api/v1/alerts/analyze/ACC-982001")
        assert_test(analyze_res["status_code"] == 200, "Risk analysis executed via /api/v1/alerts/analyze/ACC-982001")

        # Query ml-health again from admin
        res_after = adm.request("GET", "/api/v1/internal/ml-health")
        data_after = res_after["data"]
        tel_after = data_after["telemetry"]

        assert_test(tel_after["total_inferences"] >= initial_inferences + 1, "Inference telemetry count incremented after real inference")
        assert_test(tel_after["successful_inferences"] >= 1, "Successful inferences updated")
        assert_test(tel_after["avg_latency_ms"] > 0, f"Average latency updated: {tel_after['avg_latency_ms']}ms")
        assert_test(tel_after["latest_latency_ms"] is not None, f"Latest latency recorded: {tel_after['latest_latency_ms']}ms")
        assert_test(tel_after["latest_inference_time"] is not None, "Latest inference timestamp recorded")

        dist = tel_after["risk_distribution"]
        assert_test(sum(dist.values()) == tel_after["successful_inferences"], "Risk distribution sum matches successful inferences")

        print("\n====================================================")
        print(f"ALL LIVE ENDPOINT & RBAC TESTS PASSED: {passed_tests}/{total_tests} PASS")
        print("====================================================")

    finally:
        if server_process:
            print("[Teardown] Terminating test server process...")
            server_process.terminate()
            try:
                server_process.wait(timeout=3)
            except Exception:
                server_process.kill()


if __name__ == "__main__":
    run_live_tests()
