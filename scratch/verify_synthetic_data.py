"""
MuleGuard Synthetic Data Operations & Verification Runner
Validates the real PostgreSQL dataset operations endpoint, RBAC enforcement,
data quality integrity checks, ML 26-feature compatibility, and non-mutation safety.
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
from app.services.dataset_service import (
    get_real_dataset_summary,
    validate_data_quality,
    validate_ml_compatibility,
    get_synthetic_data_report,
)
from app.services.feature_engine import FEATURE_ORDER

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


def run_unit_and_quality_checks():
    print("\n[Section 1] Ground-Truth PostgreSQL Counts & Distributions...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM customers;")
            db_cust = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM accounts;")
            db_acc = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM transactions;")
            db_tx = cur.fetchone()[0]

            cur.execute("SELECT COALESCE(SUM(amount), 0), COALESCE(AVG(amount), 0) FROM transactions;")
            db_sum, db_avg = cur.fetchone()

            cur.execute("SELECT status, COUNT(*) FROM accounts GROUP BY status;")
            db_statuses = dict(cur.fetchall())

    summary = get_real_dataset_summary()

    check(summary["status"] == "Available", "Dataset status is Available")
    check(summary["database_source"] == "PostgreSQL", "Database source is PostgreSQL")
    check(summary["counts"]["customers"] == db_cust, f"Customer count matches PostgreSQL: {db_cust}")
    check(summary["counts"]["accounts"] == db_acc, f"Account count matches PostgreSQL: {db_acc}")
    check(summary["counts"]["transactions"] == db_tx, f"Transaction count matches PostgreSQL: {db_tx}")
    check(summary["counts"]["legitimate_accounts"] == db_statuses.get("Normal", 0), "Legitimate account count matches Normal status in DB")
    check(summary["counts"]["suspicious_mule_accounts"] == (db_acc - db_statuses.get("Normal", 0)), "Suspicious account count matches non-Normal status in DB")

    financial = summary["financial_summary"]
    check(abs(financial["total_transaction_value"] - float(db_sum)) < 0.01, f"Total value matches DB: {financial['total_transaction_value']}")
    check(financial["total_transaction_value_inr"].startswith("₹"), "Total value formatted in INR (₹)")
    check(abs(financial["average_transaction_value"] - round(float(db_avg), 2)) < 0.01, f"Avg value matches DB: {financial['average_transaction_value']}")

    print("\n[Section 2] Data Quality Validation Checks...")
    dq = validate_data_quality()
    check(dq["status"] == "VALID", "Overall data quality status is VALID")
    check(dq["errors"] == 0, f"Zero data quality errors detected: {dq['errors']}")
    check(dq["total_records_checked"] == (db_cust + db_acc + db_tx), f"Total records verified matches entities sum: {dq['total_records_checked']}")

    checks = dq["checks"]
    check(checks["orphan_accounts"]["passed"], "Zero orphan accounts verified")
    check(checks["orphan_transactions"]["passed"], "Zero orphan transactions verified")
    check(checks["invalid_relationships"]["passed"], "Zero invalid sender/receiver relationships")
    check(checks["negative_or_zero_amounts"]["passed"], "Zero negative/zero amounts")
    check(checks["invalid_timestamps"]["passed"], "Zero invalid timestamps")
    check(checks["duplicate_transactions"]["passed"], "Zero duplicate transaction IDs")
    check(checks["invalid_account_statuses"]["passed"], "Zero invalid account statuses")
    check(checks["missing_required_fields"]["passed"], "Zero missing required account fields")

    print("\n[Section 3] ML 26-Feature Compatibility Checks...")
    ml = validate_ml_compatibility()
    check(ml["status"] == "VALID", "ML compatibility status is VALID")
    check(ml["expected_features"] == 26, "Expected feature count is 26")
    check(ml["actual_features"] == 26, "Actual feature count is 26")
    check(ml["actual_features"] == len(FEATURE_ORDER), "Actual feature count matches FEATURE_ORDER length")
    check(ml["compatible_accounts"] == db_acc, f"All {db_acc} accounts are 100% compatible")
    check(ml["mismatched_length_count"] == 0, "Zero mismatched length feature vectors")
    check(ml["non_finite_values_count"] == 0, "Zero NaN/Infinity values across all accounts")

    print("\n[Section 4] Non-Mutation Safety on Multiple Reads...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM accounts;")
            before_acc = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM transactions;")
            before_tx = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM customers;")
            before_cust = cur.fetchone()[0]

    for _ in range(5):
        get_synthetic_data_report()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM accounts;")
            after_acc = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM transactions;")
            after_tx = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM customers;")
            after_cust = cur.fetchone()[0]

    check(before_acc == after_acc, "Account count remained identical after repeated queries (No mutation)")
    check(before_tx == after_tx, "Transaction count remained identical after repeated queries (No mutation)")
    check(before_cust == after_cust, "Customer count remained identical after repeated queries (No mutation)")

    print("\n[Section 5] Zero PII & Credential Leakage...")
    report = get_synthetic_data_report()
    report_json = json.dumps(report).lower()
    for sensitive_key in ["password", "token", "biometric", "probe_vector", "salt", "secret", "private_key"]:
        check(sensitive_key not in report_json, f"Sensitive credential '{sensitive_key}' not exposed in summary payload")

    check("phone" not in report_json, "Raw customer phone numbers not leaked")
    check("ip_address" not in report_json, "Raw customer IP addresses not leaked")
    check("address" not in report_json, "Raw physical customer addresses not leaked")


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
        res_anon = anon_client.request("GET", "/api/v1/internal/synthetic-data")
        check(res_anon["status_code"] == 401, f"Unauthenticated /synthetic-data returns 401 Unauthorized (got {res_anon['status_code']})")

        print("\n[Section 7] Investigator Role Rejection (403 Forbidden)...")
        inv_client = AuthenticatedClient()
        inv_client.login("MG-INV-001")  # Investigator
        res_inv = inv_client.request("GET", "/api/v1/internal/synthetic-data")
        check(res_inv["status_code"] == 403, f"Investigator forbidden from /synthetic-data (got {res_inv['status_code']})")

        print("\n[Section 8] Compliance Role Rejection (403 Forbidden)...")
        comp_client = AuthenticatedClient()
        comp_client.login("MG-CMP-001")  # Compliance
        res_comp = comp_client.request("GET", "/api/v1/internal/synthetic-data")
        check(res_comp["status_code"] == 403, f"Compliance forbidden from /synthetic-data (got {res_comp['status_code']})")

        print("\n[Section 9] Internal Team Access Allowed (200 OK)...")
        admin_client = AuthenticatedClient()
        admin_client.login("MG-ADM-001")  # Internal Team / Admin
        res_admin = admin_client.request("GET", "/api/v1/internal/synthetic-data")
        check(res_admin["status_code"] == 200, f"Internal Team / Admin can access /synthetic-data (got {res_admin['status_code']})")

        data = res_admin["data"]
        check(data["status"] == "Available", f"Live endpoint status is Available (got {data['status']})")
        check(data["database_source"] == "PostgreSQL", "Live endpoint confirms PostgreSQL source")
        check(data["counts"]["customers"] == 350, f"Live customer count is 350 (got {data['counts']['customers']})")
        check(data["counts"]["accounts"] == 350, f"Live account count is 350 (got {data['counts']['accounts']})")
        check(data["counts"]["transactions"] == 2732, f"Live transaction count is 2732 (got {data['counts']['transactions']})")
        check(data["data_quality"]["status"] == "VALID", "Live data quality reports VALID")
        check(data["ml_compatibility"]["status"] == "VALID", "Live ML compatibility reports VALID")
        check("financial_summary" in data, "Payload contains financial_summary block")
        check("account_distribution" in data, "Payload contains account_distribution block")
        check("generator_metadata" in data, "Payload contains generator_metadata block")

        print("\n[Section 10] On-Demand Dataset Validation Trigger (POST)...")
        res_val = admin_client.request("POST", "/api/v1/internal/synthetic-data/validate")
        check(res_val["status_code"] == 200, f"POST /synthetic-data/validate succeeds (got {res_val['status_code']})")
        check(res_val["data"]["data_quality"]["status"] == "VALID", "Re-validation confirms VALID status")

        print("\n[Section 11] Unauthorized POST Validation Rejection...")
        res_inv_post = inv_client.request("POST", "/api/v1/internal/synthetic-data/validate")
        check(res_inv_post["status_code"] == 403, f"Investigator forbidden from POST /synthetic-data/validate (got {res_inv_post['status_code']})")

    finally:
        if started_by_test and server_process:
            print("\n[Teardown] Terminating test server process...")
            server_process.terminate()
            server_process.wait(timeout=5)
            print("[Teardown] Server stopped.")


def main():
    print("=" * 52)
    print("MULEGUARD SYNTHETIC DATA VERIFICATION RUNNER")
    print("=" * 52)

    run_unit_and_quality_checks()
    run_http_endpoint_tests()

    print("\n" + "=" * 52)
    print(f"ALL SYNTHETIC DATA CHECKS PASSED: {passed_checks}/{passed_checks} PASS")
    print("=" * 52)


if __name__ == "__main__":
    main()
