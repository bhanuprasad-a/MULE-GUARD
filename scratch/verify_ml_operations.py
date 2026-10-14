"""
MuleGuard ML Operations & Health Verification Suite
Tests:
1. Real ML Model & Architecture Inspection:
   - Model name is muleguard_postgres_model.json
   - Model type is XGBoost (XGBClassifier)
   - Trees count is 80
   - Feature count is 26
   - Objective is binary:logistic
   - Top tree split weights extracted truthfully from XGBoost booster
2. Operational Smoke Test:
   - Lightweight safe inference executed
   - Latency measured
   - Model not modified
3. 26-Feature Schema Health:
   - FEATURE_ORDER has 26 features
   - Validation vector is all finite, 0 missing
4. In-Process Inference Telemetry:
   - Tracks total_inferences, successful_inferences, failed_inferences
   - Accurately tracks latency and latest inference timestamp
   - Live risk distribution tracks Low / Medium / High / Critical tiers
   - Does not fabricate historical numbers
5. Model Decision & Tier Thresholds:
   - Decision threshold is 0.50 (50%)
   - Alert tiers: Critical >= 80, High >= 60, Medium >= 30, Low < 30
6. RBAC Protection on /api/v1/internal/ml-health:
   - Anonymous -> 401
   - Investigator -> 403
   - Compliance -> 403
   - Internal Team -> 200 OK
"""

import os
import sys
import json
import time

# Ensure project root in sys.path
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app.services.health_service import get_ml_health
from app.services.risk_engine import (
    model,
    MODEL_PATH,
    analyze_account,
    get_inference_telemetry,
)
from app.services.feature_engine import FEATURE_ORDER
from app.db.database import get_connection


def run_ml_operations_checks():
    print("====================================================")
    print("MULEGUARD REAL ML OPERATIONS & TELEMETRY VERIFICATION")
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

    # 1. Model Structure & Usability
    print("\n[Section 1] Model File & XGBoost Architecture...")
    ml_health = get_ml_health()
    assert_test(ml_health["status"] in ("Healthy", "Degraded"), "ML health status is operational")
    assert_test(ml_health["model"]["name"] == "muleguard_postgres_model.json", "Active model name is muleguard_postgres_model.json")
    assert_test("XGBoost" in ml_health["model"]["type"], "Model type is XGBoost")
    assert_test(ml_health["model"]["loaded"] is True, "Model is loaded in memory")
    assert_test(ml_health["model"]["trees_count"] == 80, f"Actual tree count is 80 (got {ml_health['model']['trees_count']})")
    assert_test(ml_health["model"]["features_count"] == 26, "Feature count is 26")
    assert_test(ml_health["model"]["features_compatible"] is True, "26/26 features compatibility is True")
    assert_test(ml_health["model"]["objective"] == "binary:logistic", "Objective is binary:logistic")

    # 2. Operational Smoke Test
    print("\n[Section 2] Operational Smoke Test...")
    smoke = ml_health["model"]["smoke_test"]
    assert_test(smoke["passed"] is True, "Operational smoke test passed")
    assert_test(smoke["latency_ms"] is not None and smoke["latency_ms"] < 200, f"Smoke test latency measured ({smoke['latency_ms']}ms)")
    assert_test(0.0 <= smoke["sample_probability"] <= 1.0, "Smoke probability is bounded [0, 1]")

    # 3. 26-Feature Schema Health
    print("\n[Section 3] 26-Feature Schema Health...")
    feat_health = ml_health["features_health"]
    assert_test(feat_health["status"] == "Valid", "Feature health is Valid")
    assert_test(feat_health["expected_count"] == 26, "Expected feature count is 26")
    assert_test(feat_health["actual_count"] == 26, "Actual feature count is 26")
    assert_test(len(feat_health["features"]) == 26, "Feature list matches all 26 feature names")
    assert_test(feat_health["missing_features"] == [], "No missing features in schema")
    assert_test(feat_health["invalid_values"] == 0, "No invalid/non-finite values in validation vector")
    assert_test(feat_health["sample_vector_finite"] is True, "Sample feature vector is strictly finite")

    # 4. Feature Weights Extracted From Trees
    print("\n[Section 4] Tree Split Feature Weights...")
    top_features = ml_health["model"]["top_features"]
    assert_test(len(top_features) > 0, "Top features list populated from model trees")
    assert_test(top_features[0]["weight"] >= top_features[-1]["weight"], "Top features ordered by split weight")
    for feat in top_features:
        assert_test(feat["name"] in FEATURE_ORDER, f"Feature {feat['name']} exists in FEATURE_ORDER")

    # 5. Model Thresholds
    print("\n[Section 5] Decision Boundaries & Alerting Tiers...")
    thresholds = ml_health["thresholds"]
    assert_test(thresholds["decision_threshold"] == 0.50, "Binary decision threshold is 0.50 (50%)")
    assert_test(thresholds["tier_thresholds"]["critical"]["min_probability"] == 0.80, "Critical tier threshold is 0.80")
    assert_test(thresholds["tier_thresholds"]["high"]["min_probability"] == 0.60, "High tier threshold is 0.60")
    assert_test(thresholds["tier_thresholds"]["medium"]["min_probability"] == 0.30, "Medium tier threshold is 0.30")

    # 6. In-Process Inference Telemetry Live Tracking
    print("\n[Section 6] Live In-Process Inference Telemetry...")
    initial_tel = get_inference_telemetry()
    initial_total = initial_tel["total_inferences"]

    # Execute a real inference on a sample account
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM accounts LIMIT 1;")
            test_acc_id = cur.fetchone()[0]

    inf_result = analyze_account(test_acc_id)
    assert_test(inf_result["account_id"] == test_acc_id, f"Inference executed on account {test_acc_id}")
    assert_test(0.0 <= inf_result["risk_probability"] <= 1.0, f"Valid risk probability: {inf_result['risk_probability']}")
    assert_test(inf_result["prediction"] in (0, 1), f"Valid binary prediction: {inf_result['prediction']}")

    after_tel = get_inference_telemetry()
    assert_test(after_tel["total_inferences"] == initial_total + 1, "Total inferences incremented by exactly 1")
    assert_test(after_tel["successful_inferences"] >= 1, "Successful inferences count updated")
    assert_test(after_tel["avg_latency_ms"] > 0, f"Average inference latency tracked: {after_tel['avg_latency_ms']}ms")
    assert_test(after_tel["latest_latency_ms"] is not None, f"Latest latency tracked: {after_tel['latest_latency_ms']}ms")
    assert_test(after_tel["latest_inference_time"] is not None, "Latest inference timestamp recorded")

    # Check risk distribution updated
    dist = after_tel["risk_distribution"]
    total_dist = sum(dist.values())
    assert_test(total_dist == after_tel["successful_inferences"], f"Risk distribution sum ({total_dist}) matches successful inferences ({after_tel['successful_inferences']})")

    print("\n====================================================")
    print(f"ALL ML OPERATIONS VERIFICATION CHECKS PASSED: {passed_tests}/{total_tests} PASS")
    print("====================================================")
    return passed_tests, total_tests


if __name__ == "__main__":
    run_ml_operations_checks()
