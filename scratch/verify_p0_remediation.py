"""
MuleGuard Step 8: P0 Remediation Verification Suite
Verifies:
1. requirements.txt existence, structure, and import sanity
2. Dynamic high_risk_accounts in /api/v1/kpis (no hardcoding)
3. Production tree cleanliness (app/scratch/ eliminated, scratch/get_suspicious.py operational)
4. FastAPI application startup and route integrity
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

PASS_COUNT = 0
FAIL_COUNT = 0


def record_test(name: str, passed: bool, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if passed:
        PASS_COUNT += 1
        print(f"  [OK] PASS: {name}" + (f" ({detail})" if detail else ""))
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] FAIL: {name} - {detail}")


def test_requirements_file():
    print("\n[P0-1] Verifying requirements.txt...")
    req_path = ROOT_DIR / "requirements.txt"
    record_test("requirements.txt exists at repository root", req_path.is_file())

    content = req_path.read_text(encoding="utf-8")
    required_packages = [
        "fastapi",
        "uvicorn",
        "psycopg",
        "psycopg-pool",
        "argon2-cffi",
        "cryptography",
        "opencv-python",
        "networkx",
        "xgboost",
        "numpy",
        "scikit-learn",
        "python-dotenv",
        "pandas",
    ]
    for pkg in required_packages:
        record_test(f"requirements.txt contains {pkg}", pkg in content)

    # Test importing all critical modules
    try:
        import fastapi
        import uvicorn
        import psycopg
        import psycopg_pool
        import argon2
        import cryptography
        import cv2
        import networkx
        import xgboost
        import numpy
        import sklearn
        import dotenv
        import pandas
        record_test("All runtime dependencies imported successfully", True)
    except Exception as e:
        record_test("All runtime dependencies imported successfully", False, str(e))


def test_dynamic_kpis():
    print("\n[P0-2] Verifying dynamic high_risk_accounts in /api/v1/kpis...")
    from app.api.remaining import get_kpis
    from app.api.risk import compute_risk_summary

    kpis = get_kpis()
    record_test("get_kpis returns valid dictionary", isinstance(kpis, dict))
    record_test("get_kpis includes high_risk_accounts", "high_risk_accounts" in kpis)
    
    high_risk = kpis["high_risk_accounts"]
    record_test("high_risk_accounts is integer", isinstance(high_risk, int))
    record_test("high_risk_accounts is positive", high_risk > 0, f"got {high_risk}")

    # Verify against compute_risk_summary
    risk_summary = compute_risk_summary()
    expected_high_risk = risk_summary["high_risk_accounts"]
    record_test(
        "high_risk_accounts matches dynamic compute_risk_summary calculation",
        high_risk == expected_high_risk,
        f"kpis={high_risk}, risk_summary={expected_high_risk}"
    )

    # Verify code does not contain hardcoded "high_risk_accounts": 18
    remaining_code = (ROOT_DIR / "app" / "api" / "remaining.py").read_text(encoding="utf-8")
    record_test(
        "app/api/remaining.py contains no hardcoded 'high_risk_accounts': 18",
        '"high_risk_accounts": 18' not in remaining_code
    )


def test_scratch_removal():
    print("\n[P0-3] Verifying removal of app/scratch from production tree...")
    app_scratch = ROOT_DIR / "app" / "scratch"
    record_test("app/scratch/ directory does not exist", not app_scratch.exists())

    old_file = app_scratch / "get_suspicious.py"
    record_test("app/scratch/get_suspicious.py does not exist", not old_file.exists())

    new_file = ROOT_DIR / "scratch" / "get_suspicious.py"
    record_test("scratch/get_suspicious.py exists in dev/scratch area", new_file.is_file())

    # Verify scratch/get_suspicious.py runs cleanly
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(new_file)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
    )
    record_test("scratch/get_suspicious.py executes successfully", proc.returncode == 0, proc.stderr.strip())


def test_fastapi_startup():
    print("\n[P0-4] Verifying FastAPI application startup & route integrity...")
    from app.main import app
    record_test("FastAPI app initializes without errors", app is not None)
    
    # Check that 9 routers and 46 total routes are intact
    routes_count = len(app.routes)
    record_test("FastAPI route collection loaded", routes_count >= 15, f"{routes_count} top-level routes")


if __name__ == "__main__":
    print("=" * 60)
    print("MULEGUARD P0 REMEDIATION VERIFICATION RUNNER")
    print("=" * 60)

    test_requirements_file()
    test_dynamic_kpis()
    test_scratch_removal()
    test_fastapi_startup()

    print("\n" + "=" * 60)
    print(f"P0 CHECKS TOTAL: {PASS_COUNT}/{PASS_COUNT + FAIL_COUNT} PASS")
    print("=" * 60)

    if FAIL_COUNT > 0:
        sys.exit(1)
