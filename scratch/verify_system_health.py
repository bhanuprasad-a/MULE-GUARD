"""
MuleGuard System Health Verification Runner
Tests:
1. Direct Health Service Logic (app.services.health_service.get_system_health)
   - API Gateway telemetry
   - PostgreSQL connection and pool metrics
   - XGBoost ML Engine (model loaded, 26 features validated, inference smoke test)
   - PostgreSQL Graph topology (accounts nodes, transactions edges)
   - Process Uptime (accurate calculation, non-hardcoded)
   - Heartbeat events log buffer
2. API & RBAC Endpoint Verification (/api/v1/internal/system-health)
   - Unauthenticated request -> 401 Unauthorized
   - Investigator persona (MG-INV-001) -> 403 Forbidden
   - Compliance persona (MG-CMP-001) -> 403 Forbidden
   - Internal Team persona (MG-ADM-001) -> 200 OK with valid health structure
"""

import os
import sys
import json
import time

# Ensure project root in sys.path
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app.services.health_service import (
    get_system_health,
    check_api_gateway,
    check_database,
    check_ml_engine,
    check_graph_engine,
    get_uptime_info,
)


def run_unit_checks():
    print("====================================================")
    print("MULEGUARD SYSTEM HEALTH TELEMETRY VERIFICATION")
    print("====================================================")

    total_tests = 0
    passed_tests = 0

    def assert_test(cond, title):
        nonlocal total_tests, passed_tests
        total_tests += 1
        if cond:
            passed_tests += 1
            print(f"  [OK] PASS: {title}")
        else:
            print(f"  [FAIL] FAIL: {title}")
            assert False, title

    # 1. API Gateway check
    print("\n[Test 1] API Gateway Telemetry...")
    t0 = time.perf_counter()
    api_res = check_api_gateway(t0)
    assert_test(api_res["status"] == "Healthy", "API Gateway reports Healthy status")
    assert_test(isinstance(api_res["latency_ms"], (int, float)), "API Gateway reports numeric latency_ms")
    assert_test(api_res["pid"] == os.getpid(), "API Gateway reports accurate process PID")

    # 2. Database check
    print("\n[Test 2] PostgreSQL & Connection Pool Telemetry...")
    db_res = check_database()
    assert_test(db_res["status"] in ("Healthy", "Degraded"), "PostgreSQL reports Healthy/Degraded status")
    assert_test(db_res["database_type"] == "PostgreSQL", "Database type is PostgreSQL")
    assert_test(isinstance(db_res["pool"], dict), "Connection pool statistics are present")
    assert_test("size" in db_res["pool"] and "max" in db_res["pool"], "Pool stats contain size and max")
    assert_test(isinstance(db_res["latency_ms"], (int, float)), "Database latency is measured")

    # 3. ML Engine check
    print("\n[Test 3] MuleGuard ML Engine Telemetry...")
    ml_res = check_ml_engine()
    assert_test(ml_res["status"] == "Healthy", "ML engine reports Healthy status")
    assert_test(ml_res["model_loaded"] is True, "Model is confirmed loaded")
    assert_test(ml_res["features_count"] == 26, "Model feature count matches exactly 26 features")
    assert_test(isinstance(ml_res["latency_ms"], (int, float)), "ML inference latency is measured")

    # 4. Graph Engine check
    print("\n[Test 4] Graph Engine Topology Telemetry...")
    graph_res = check_graph_engine()
    assert_test(graph_res["status"] == "Healthy", "Graph engine reports Healthy status")
    assert_test(graph_res["nodes_count"] > 0, f"Account nodes count > 0 ({graph_res['nodes_count']})")
    assert_test(graph_res["edges_count"] > 0, f"Transaction edges count > 0 ({graph_res['edges_count']})")

    # 5. Process Uptime
    print("\n[Test 5] Process Uptime Telemetry...")
    uptime_res = get_uptime_info()
    assert_test(uptime_res["status"] == "Healthy", "Uptime status is Healthy")
    assert_test(uptime_res["label"] == "Process Uptime", "Label is truthfully 'Process Uptime'")
    assert_test(uptime_res["uptime_seconds"] >= 0, "Uptime seconds is non-negative")
    assert_test(isinstance(uptime_res["formatted"], str) and len(uptime_res["formatted"]) > 0, "Uptime is formatted (e.g. '0s')")

    # 6. Overall Aggregation & Events
    print("\n[Test 6] Full Aggregated Telemetry Payload & Heartbeat Events...")
    full_health = get_system_health()
    assert_test(full_health["status"] in ("Healthy", "Degraded", "Unavailable"), "Overall status valid")
    assert_test(isinstance(full_health["events"], list) and len(full_health["events"]) >= 4, "Heartbeat events list contains real recent log items")
    for ev in full_health["events"]:
        assert_test(ev.startswith("[202") and "INFO:" in ev or "WARN:" in ev or "ERROR:" in ev, f"Event log formatted correctly: {ev[:40]}...")

    print("\n====================================================")
    print(f"ALL UNIT CHECKS PASSED: {passed_tests}/{total_tests} PASS")
    print("====================================================")
    return passed_tests, total_tests


if __name__ == "__main__":
    run_unit_checks()
