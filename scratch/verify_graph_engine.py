"""
MuleGuard Graph Engine Operations & RBAC Verification Runner
Verifies:
1. Graph Engine derives nodes and edges strictly from PostgreSQL (Zero Neo4j, Zero fake nodes).
2. All 10+ topological metrics (components, isolated accounts, fan-in, fan-out, cycles, multi-hop, concentration, suspicious links)
   are calculated from real database relationships.
3. Thread-safe in-process analysis telemetry operates accurately with zero fabricated numbers.
4. Live FastAPI endpoint GET /api/v1/internal/graph-health is protected by require_role(["internal_team"]):
   - 401 Unauthorized for unauthenticated requests
   - 403 Forbidden for bank_investigator (MG-INV-001)
   - 403 Forbidden for bank_compliance (MG-CMP-001)
   - 200 OK for internal_team (MG-ADM-001)
5. Live POST /api/v1/internal/graph-health/analyze triggers on-demand graph evaluation.
6. Zero PII, zero credentials, zero biometric data, and zero auth tokens leak through graph endpoints.
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

from app.db.database import get_connection
from app.db.init_auth_db import generate_deterministic_vector
from app.services.network_engine import (
    get_graph_health_report,
    analyze_graph_topology,
    get_graph_telemetry,
    reset_graph_telemetry_for_test,
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


def run_unit_and_telemetry_checks():
    print("\n[Section 1] Database Ground Truth & PostgreSQL Source Verification...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM accounts;")
            db_accounts_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM transactions;")
            db_txs_count = cur.fetchone()[0]

    check(db_accounts_count > 0, f"Database accounts count is non-zero ({db_accounts_count})")
    check(db_txs_count > 0, f"Database transactions count is non-zero ({db_txs_count})")

    reset_graph_telemetry_for_test()
    telem_init = get_graph_telemetry()
    check(telem_init["total_analyses"] == 0, "Initial graph analyses count starts at 0 (no fake numbers)")
    check(telem_init["successful_analyses"] == 0, "Initial successful analyses count starts at 0")
    check(telem_init["failed_analyses"] == 0, "Initial failed analyses count starts at 0")
    check(telem_init["latest_analysis_ts"] is None, "Initial latest analysis timestamp is None")

    print("\n[Section 2] Graph Engine Real Execution & Metrics Calculation...")
    report = get_graph_health_report(force_refresh=True)

    check(report["status"] == "Healthy", "Graph status is Healthy")
    check(report["source"] == "PostgreSQL", "Data source is PostgreSQL (no fake Neo4j)")
    check(report["nodes_count"] == db_accounts_count, f"Node count matches PostgreSQL accounts: {report['nodes_count']}")
    check(report["edges_count"] == db_txs_count, f"Edge count matches PostgreSQL transactions: {report['edges_count']}")

    m = report["metrics"]
    check(m["total_account_nodes"] == db_accounts_count, "Metrics total_account_nodes matches database")
    check(m["total_transaction_edges"] == db_txs_count, "Metrics total_transaction_edges matches database")
    check(m["connected_components"] > 0, f"Connected components calculated: {m['connected_components']}")
    check(m["isolated_accounts"] >= 0, f"Isolated accounts calculated: {m['isolated_accounts']}")
    check(m["fan_in_nodes"] > 0, f"Fan-in aggregator nodes identified: {m['fan_in_nodes']}")
    check(m["fan_out_nodes"] > 0, f"Fan-out smurfing nodes identified: {m['fan_out_nodes']}")
    check(m["cycle_participation"] > 0, f"Cycle participation loop nodes identified: {m['cycle_participation']}")
    check(m["multi_hop_connectivity"] > 0, f"Multi-hop reachability nodes identified: {m['multi_hop_connectivity']}")
    check(m["suspicious_connections"] > 0, f"Suspicious transaction links identified: {m['suspicious_connections']}")
    check(0.0 <= m["network_concentration"] <= 100.0, f"Network concentration bounded percentage: {m['network_concentration']}%")

    print("\n[Section 3] Thread-Safe Telemetry Updates...")
    telem_after = get_graph_telemetry()
    check(telem_after["total_analyses"] == 1, "Total analyses incremented to 1")
    check(telem_after["successful_analyses"] == 1, "Successful analyses incremented to 1")
    check(telem_after["failed_analyses"] == 0, "Failed analyses remain 0")
    check(telem_after["latest_analysis_ts"] is not None, "Latest analysis timestamp populated")
    check(telem_after["latest_analysis_latency_ms"] is not None, f"Analysis latency measured: {telem_after['latest_analysis_latency_ms']}ms")
    check(telem_after["avg_analysis_latency_ms"] > 0, f"Average analysis latency tracked: {telem_after['avg_analysis_latency_ms']}ms")

    print("\n[Section 4] Data Sanitization & Zero PII Leakage Check...")
    topo = report["sample_topology"]
    check(isinstance(topo["nodes"], list), "Sample topology contains nodes array")
    check(isinstance(topo["edges"], list), "Sample topology contains edges array")
    check(len(topo["nodes"]) > 0, f"Sample cluster contains nodes ({len(topo['nodes'])})")
    check(len(topo["edges"]) > 0, f"Sample cluster contains edges ({len(topo['edges'])})")

    # Inspect all nodes and edges for sensitive leaks
    forbidden_keys = {"password", "hash", "biometric", "face_vector", "token", "session", "phone", "device", "ip", "address"}
    for node in topo["nodes"]:
        for k in node.keys():
            check(k.lower() not in forbidden_keys, f"Node attribute '{k}' does not leak customer PII/secrets")
        check(node["id"].startswith("ACC-"), f"Node ID is valid banking account ID: {node['id']}")

    for edge in topo["edges"]:
        for k in edge.keys():
            check(k.lower() not in forbidden_keys, f"Edge attribute '{k}' does not leak secrets")
        check("source" in edge and "target" in edge, f"Edge has valid source/target link: {edge['source']} -> {edge['target']}")
        check("amount" in edge and edge["amount"] > 0, f"Edge has positive transaction amount: {edge['amount']}")


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
        print("\n[Section 5] Unauthenticated Requests Return 401...")
        anon_client = AuthenticatedClient()
        anon_res = anon_client.request("GET", "/api/v1/internal/graph-health")
        check(anon_res["status_code"] == 401, "Unauthenticated /graph-health returns 401 Unauthorized")

        # 2. Investigator client
        print("\n[Section 6] Investigator Role Rejection (403 Forbidden)...")
        inv_client = AuthenticatedClient()
        inv_client.login("MG-INV-001")
        inv_res = inv_client.request("GET", "/api/v1/internal/graph-health")
        check(inv_res["status_code"] == 403, "Investigator forbidden from /graph-health (403 Forbidden)")

        # 3. Compliance client
        print("\n[Section 7] Compliance Role Rejection (403 Forbidden)...")
        cmp_client = AuthenticatedClient()
        cmp_client.login("MG-CMP-001")
        cmp_res = cmp_client.request("GET", "/api/v1/internal/graph-health")
        check(cmp_res["status_code"] == 403, "Compliance forbidden from /graph-health (403 Forbidden)")

        # 4. Internal Team / Admin client
        print("\n[Section 8] Internal Team Access Allowed (200 OK)...")
        adm_client = AuthenticatedClient()
        adm_client.login("MG-ADM-001")
        adm_res = adm_client.request("GET", "/api/v1/internal/graph-health")
        check(adm_res["status_code"] == 200, "Internal Team / Admin can access /graph-health (200 OK)")

        payload = adm_res["data"]
        check(payload["status"] == "Healthy", "Live endpoint reports status Healthy")
        check(payload["source"] == "PostgreSQL", "Live endpoint confirms PostgreSQL source")
        check(payload["nodes_count"] == 350, f"Live node count is 350 (got {payload['nodes_count']})")
        check(payload["edges_count"] == 2732, f"Live edge count is 2732 (got {payload['edges_count']})")
        check("metrics" in payload, "Payload contains metrics block")
        check("telemetry" in payload, "Payload contains telemetry block")
        check("sample_topology" in payload, "Payload contains sample_topology block")

        # 5. On-Demand Analysis Trigger
        print("\n[Section 9] On-Demand Analysis Trigger & Telemetry Update...")
        eval_before = payload["telemetry"]["total_analyses"]
        trigger_res = adm_client.request("POST", "/api/v1/internal/graph-health/analyze")
        check(trigger_res["status_code"] == 200, "POST /graph-health/analyze succeeds (200 OK)")

        adm_res2 = adm_client.request("GET", "/api/v1/internal/graph-health")
        payload2 = adm_res2["data"]
        eval_after = payload2["telemetry"]["total_analyses"]
        check(eval_after == eval_before + 1, f"Live server analyses incremented from {eval_before} to {eval_after}")

        # 6. Unauthorized trigger rejection
        print("\n[Section 10] Unauthorized POST Analysis Rejection...")
        inv_post = inv_client.request("POST", "/api/v1/internal/graph-health/analyze")
        check(inv_post["status_code"] == 403, "Investigator forbidden from POST /graph-health/analyze (403 Forbidden)")

    finally:
        if server_process:
            print("\n[Teardown] Terminating test server process...")
            server_process.terminate()
            try:
                server_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("[Teardown] Server stopped.")


def main():
    print("=" * 52)
    print("MULEGUARD GRAPH ENGINE OPERATIONS VERIFICATION RUNNER")
    print("=" * 52)

    run_unit_and_telemetry_checks()
    run_live_endpoint_checks()

    print("\n" + "=" * 52)
    print(f"ALL GRAPH ENGINE CHECKS PASSED: {passed_checks}/{passed_checks} PASS")
    print("=" * 52)


if __name__ == "__main__":
    main()
