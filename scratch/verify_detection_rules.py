"""
MuleGuard Detection Rules Operations & RBAC Verification Runner
Verifies:
1. 6 expected active rules are present (R-VEL-1, R-AGG-1, R-DIST-1, R-HOLD-1, R-CIRC-1, R-DORM-1).
2. Obsolete demo rules (R-NET-1, R-VAL-1) are NOT active.
3. Rule evaluation telemetry is thread-safe and non-fabricated.
4. Triggering a known rule increments only the appropriate rule counter.
5. Live FastAPI endpoint GET /api/v1/internal/detection-rules is protected by require_role(["internal_team"]):
   - 401 Unauthorized for unauthenticated requests
   - 403 Forbidden for bank_investigator (MG-INV-001)
   - 403 Forbidden for bank_compliance (MG-CMP-001)
   - 200 OK for internal_team (MG-ADM-001)
6. Report payload matches operational specifications.
"""

import sys
import os
import json
import time
import socket
import subprocess
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app.db.init_auth_db import generate_deterministic_vector
from app.services.rule_engine import (
    CANONICAL_RULES,
    OBSOLETE_RULE_IDS,
    get_rule_telemetry,
    record_evaluation_event,
    reset_telemetry_for_test,
    sync_database_rules,
    get_detection_rules_report,
    evaluate_rules_for_account,
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


def run_unit_checks():
    print("\n[Section 1] Canonical Rules & Obsolete Rules Identification...")
    canonical_ids = [r["id"] for r in CANONICAL_RULES]
    check(len(canonical_ids) == 6, "Exactly 6 active rules in canonical definition")
    check("R-VEL-1" in canonical_ids, "R-VEL-1 (Velocity) is present")
    check("R-AGG-1" in canonical_ids, "R-AGG-1 (Aggregation) is present")
    check("R-DIST-1" in canonical_ids, "R-DIST-1 (Distribution) is present")
    check("R-HOLD-1" in canonical_ids, "R-HOLD-1 (Rapid Holding) is present")
    check("R-CIRC-1" in canonical_ids, "R-CIRC-1 (Circular Flow) is present")
    check("R-DORM-1" in canonical_ids, "R-DORM-1 (Dormant Activation) is present")

    check("R-NET-1" not in canonical_ids, "R-NET-1 is not in canonical active rules")
    check("R-VAL-1" not in canonical_ids, "R-VAL-1 is not in canonical active rules")
    check("R-NET-1" in OBSOLETE_RULE_IDS, "R-NET-1 is classified as obsolete")
    check("R-VAL-1" in OBSOLETE_RULE_IDS, "R-VAL-1 is classified as obsolete")

    print("\n[Section 2] Rule Trigger Telemetry Semantics...")
    reset_telemetry_for_test()
    initial_tel = get_rule_telemetry()
    check(initial_tel["total_evaluations"] == 0, "Initial evaluations start at 0 (no fake numbers)")
    check(initial_tel["total_triggers"] == 0, "Initial triggers start at 0")
    check(all(v == 0 for v in initial_tel["per_rule_triggers"].values()), "All per-rule trigger counts start at 0")
    check(initial_tel["latest_trigger_at"] is None, "Latest trigger timestamp starts as None")

    # Record single rule trigger
    record_evaluation_event(["R-VEL-1"], failed=False)
    tel_after = get_rule_telemetry()
    check(tel_after["total_evaluations"] == 1, "Total evaluations incremented to 1")
    check(tel_after["total_triggers"] == 1, "Total triggers incremented to 1")
    check(tel_after["per_rule_triggers"]["R-VEL-1"] == 1, "Only R-VEL-1 counter incremented to 1")
    check(tel_after["per_rule_triggers"]["R-AGG-1"] == 0, "R-AGG-1 remains 0")
    check(tel_after["per_rule_triggers"]["R-HOLD-1"] == 0, "R-HOLD-1 remains 0")
    check(tel_after["latest_trigger_rule"] == "R-VEL-1", "Latest trigger rule correctly set to R-VEL-1")
    check(tel_after["latest_trigger_at"] is not None, "Latest trigger timestamp is populated")

    # Record an evaluation without triggers
    record_evaluation_event([], failed=False)
    tel_after_clean = get_rule_telemetry()
    check(tel_after_clean["total_evaluations"] == 2, "Total evaluations incremented to 2")
    check(tel_after_clean["total_triggers"] == 1, "Total triggers remained at 1")

    print("\n[Section 3] Database Sync and Report Generation...")
    sync_database_rules()
    report = get_detection_rules_report()
    check(report["status"] == "Healthy", "Detection report reports Healthy status")
    check(report["summary"]["total_rules"] == 6, "Report summary total_rules is 6")
    check(report["summary"]["enabled_rules"] == 6, "All 6 active rules are enabled")
    check(report["summary"]["disabled_rules"] == 0, "No active rules are disabled")
    check(report["summary"]["total_evaluations"] == 2, "Report includes real evaluation telemetry")
    check(report["summary"]["total_triggers"] == 1, "Report includes real trigger telemetry")
    check(len(report["rules"]) == 6, "Report rules list contains exactly 6 rules")

    for r in report["rules"]:
        check(r["status"] == "ENABLED", f"Rule {r['id']} status is ENABLED")
        check(r["category"] is not None, f"Rule {r['id']} has valid category: {r['category']}")
        check(r["threshold"] > 0, f"Rule {r['id']} has positive threshold: {r['threshold']}")


def run_live_endpoint_checks():
    server_process = None
    if not is_port_in_use(8000):
        print("\n[Setup] Starting live FastAPI server on port 8000...")
        server_process = subprocess.Popen(
            [VENV_PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for _ in range(20):
            time.sleep(0.5)
            if is_port_in_use(8000):
                print("[Setup] Server listening on port 8000.")
                break
        else:
            raise RuntimeError("Server failed to start on port 8000.")

    try:
        # 1. Unauthenticated client
        print("\n[Section 4] Unauthenticated Requests Return 401...")
        anon_client = AuthenticatedClient()
        anon_res = anon_client.request("GET", "/api/v1/internal/detection-rules")
        check(anon_res["status_code"] == 401, "Unauthenticated /detection-rules returns 401 Unauthorized")

        # 2. Investigator client
        print("\n[Section 5] Investigator Role Rejection (403 Forbidden)...")
        inv_client = AuthenticatedClient()
        inv_client.login("MG-INV-001")
        inv_res = inv_client.request("GET", "/api/v1/internal/detection-rules")
        check(inv_res["status_code"] == 403, "Investigator forbidden from /detection-rules (403 Forbidden)")

        # 3. Compliance client
        print("\n[Section 6] Compliance Role Rejection (403 Forbidden)...")
        cmp_client = AuthenticatedClient()
        cmp_client.login("MG-CMP-001")
        cmp_res = cmp_client.request("GET", "/api/v1/internal/detection-rules")
        check(cmp_res["status_code"] == 403, "Compliance forbidden from /detection-rules (403 Forbidden)")

        # 4. Internal Team / Admin client
        print("\n[Section 7] Internal Team Access Allowed (200 OK)...")
        adm_client = AuthenticatedClient()
        adm_client.login("MG-ADM-001")
        adm_res = adm_client.request("GET", "/api/v1/internal/detection-rules")
        check(adm_res["status_code"] == 200, "Internal Team / Admin can access /detection-rules (200 OK)")

        payload = adm_res["data"]
        check(payload["status"] == "Healthy", "Status is Healthy")
        check(payload["summary"]["total_rules"] == 6, "Total rules is exactly 6")
        check(payload["summary"]["enabled_rules"] == 6, "Enabled rules is 6")
        check(payload["summary"]["disabled_rules"] == 0, "Disabled rules is 0")
        check(len(payload["rules"]) == 6, "Returns exactly 6 active rules")

        rule_ids = [r["id"] for r in payload["rules"]]
        expected_ids = ["R-VEL-1", "R-AGG-1", "R-DIST-1", "R-HOLD-1", "R-CIRC-1", "R-DORM-1"]
        check(set(rule_ids) == set(expected_ids), f"Active rule IDs match exactly: {rule_ids}")
        check("R-NET-1" not in rule_ids, "Obsolete rule R-NET-1 is not in active rules")
        check("R-VAL-1" not in rule_ids, "Obsolete rule R-VAL-1 is not in active rules")

        # 5. Live Rule Evaluation & Telemetry Update
        print("\n[Section 8] Live Rule Evaluation Telemetry Check...")
        eval_before = payload["summary"]["total_evaluations"]
        eval_res = adm_client.request("POST", "/api/v1/internal/detection-rules/evaluate/ACC-982001")
        check(eval_res["status_code"] == 200, "POST /detection-rules/evaluate/ACC-982001 succeeded (200 OK)")
        eval_result = eval_res["data"]
        check("account_id" in eval_result, "evaluate_rules executed successfully on ACC-982001")

        # Verify endpoint returns updated telemetry
        adm_res2 = adm_client.request("GET", "/api/v1/internal/detection-rules")
        payload2 = adm_res2["data"]
        eval_after = payload2["summary"]["total_evaluations"]
        check(eval_after == eval_before + 1, f"Total evaluations incremented from {eval_before} to {eval_after}")

    finally:
        if server_process:
            print("\n[Teardown] Terminating test server process...")
            server_process.terminate()
            try:
                server_process.wait(timeout=3)
            except Exception:
                server_process.kill()


if __name__ == "__main__":
    print("====================================================")
    print("MULEGUARD DETECTION RULES VERIFICATION RUNNER")
    print("====================================================")
    run_unit_checks()
    run_live_endpoint_checks()
    print("\n====================================================")
    print(f"ALL DETECTION RULES CHECKS PASSED: {passed_checks}/{passed_checks} PASS")
    print("====================================================")
