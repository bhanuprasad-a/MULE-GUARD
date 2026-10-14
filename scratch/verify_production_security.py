"""
MuleGuard Production Security Remediation Verification Suite
Uses standard library urllib.request and subprocess to verify:
1. Environment configuration
2. Demo biometric endpoints disabled in production (404)
3. Synthetic probe vectors blocked in production (400)
4. MULEGUARD_BIO_KEY enforcement in production (fails startup if missing/invalid)
5. CORS wildcard elimination & explicit allowed origins
6. Session cookie Secure flag based on environment
7. Security headers (nosniff, DENY, strict-origin-when-cross-origin, HSTS in prod)
8. API docs (/docs, /redoc, /openapi.json) disabled in production (404)
"""

import os
import sys

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import time
import subprocess
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

passed = 0
failed = 0

def check(condition: bool, msg: str):
    global passed, failed
    if condition:
        print(f"  \033[92m[PASS]\033[0m {msg}")
        passed += 1
    else:
        print(f"  \033[91m[FAIL]\033[0m {msg}")
        failed += 1


print("=" * 70)
print("MULEGUARD PRODUCTION SECURITY VERIFICATION RUNNER")
print("=" * 70)

DEV_URL = "http://127.0.0.1:8000"

# ==============================================================================
# SECTION 1: DEVELOPMENT ENVIRONMENT CHECKS (Live Development Server)
# ==============================================================================
print("\n[SECTION 1: Development Environment (Live Server http://127.0.0.1:8000)]")

# 1.1 Config constants check
from app.core.config import ENVIRONMENT, IS_PRODUCTION, COOKIE_SECURE, ALLOWED_ORIGINS
check(ENVIRONMENT == "development", f"ENVIRONMENT is '{ENVIRONMENT}' (expected 'development')")
check(IS_PRODUCTION is False, "IS_PRODUCTION is False in local environment")
check(COOKIE_SECURE is False, "Session cookie Secure=False in dev so local HTTP login works")
check("*" not in ALLOWED_ORIGINS, "CORS allowed origins does NOT contain wildcard '*'")
check("http://127.0.0.1:8000" in ALLOWED_ORIGINS, "CORS allowed origins includes local dev origin http://127.0.0.1:8000")

# 1.2 Security headers on live dev server
req = urllib.request.Request(f"{DEV_URL}/health")
try:
    with urllib.request.urlopen(req) as resp:
        check(resp.status == 200, "Health check returns 200 OK")
        headers = dict(resp.headers)
        check(headers.get("x-content-type-options") == "nosniff", "X-Content-Type-Options: nosniff present")
        check(headers.get("x-frame-options") == "DENY", "X-Frame-Options: DENY present")
        check(headers.get("referrer-policy") == "strict-origin-when-cross-origin", "Referrer-Policy: strict-origin-when-cross-origin present")
        check("strict-transport-security" not in headers, "HSTS omitted in development HTTP")
except Exception as e:
    check(False, f"Failed to connect to dev server at {DEV_URL}/health: {e}")

# 1.3 Documentation available in development
try:
    with urllib.request.urlopen(f"{DEV_URL}/docs") as resp:
        check(resp.status == 200, "Swagger UI (/docs) is accessible in development (200)")
except Exception as e:
    check(False, f"Swagger /docs check failed: {e}")

try:
    with urllib.request.urlopen(f"{DEV_URL}/openapi.json") as resp:
        check(resp.status == 200, "OpenAPI schema (/openapi.json) is accessible in development (200)")
except Exception as e:
    check(False, f"OpenAPI schema check failed: {e}")

# 1.4 Demo endpoints available in development
try:
    demo_req = urllib.request.Request(
        f"{DEV_URL}/api/v1/auth/demo-probe-vector",
        data=json.dumps({"employee_id": "MG-INV-001"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(demo_req) as resp:
        check(resp.status == 200, "POST /api/v1/auth/demo-probe-vector available in dev (200)")
except Exception as e:
    check(False, f"Demo probe vector failed in dev: {e}")

try:
    with urllib.request.urlopen(f"{DEV_URL}/api/v1/auth/demo-sample-face") as resp:
        check(resp.status == 200, "GET /api/v1/auth/demo-sample-face available in dev (200)")
except Exception as e:
    check(False, f"Demo sample face failed in dev: {e}")

# 1.5 CORS preflight does not return wildcard with credentials
try:
    cors_req = urllib.request.Request(
        f"{DEV_URL}/api/v1/auth/stage1-login",
        method="OPTIONS",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "POST"
        }
    )
    with urllib.request.urlopen(cors_req) as resp:
        origin_header = resp.headers.get("access-control-allow-origin")
        cred_header = resp.headers.get("access-control-allow-credentials")
        check(origin_header == "http://127.0.0.1:8000", f"CORS returns explicit origin '{origin_header}', NOT wildcard")
        check(cred_header == "true", "CORS allows credentials")
except Exception as e:
    check(False, f"CORS preflight failed: {e}")


# ==============================================================================
# SECTION 2: PRODUCTION ENVIRONMENT VALIDATION
# ==============================================================================
print("\n[SECTION 2: Production Environment Enforcement Tests]")

# 2.1 Test MULEGUARD_BIO_KEY Startup Failure in Production
print("\n--- Sub-test 2.1: MULEGUARD_BIO_KEY Enforcement ---")

# Missing key test
code_missing_key = """
import os
os.environ["ENVIRONMENT"] = "production"
os.environ.pop("MULEGUARD_BIO_KEY", None)
try:
    from app.services.security import BIO_ENCRYPTION_KEY
    print("UNEXPECTED_SUCCESS")
except RuntimeError as e:
    if "CRITICAL SECURITY CONFIGURATION ERROR" in str(e):
        print("EXPECTED_FAIL_MISSING")
    else:
        print("OTHER_ERROR:", e)
"""
proc = subprocess.run(
    [sys.executable, "-c", code_missing_key],
    capture_output=True,
    text=True,
    cwd="e:\\PROJECTS\\MULE GUARD",
    env=dict(os.environ, PYTHONPATH="e:\\PROJECTS\\MULE GUARD")
)
check("EXPECTED_FAIL_MISSING" in proc.stdout, "Startup correctly FAILS when MULEGUARD_BIO_KEY is missing in production")

# Invalid length key test (not 32 bytes)
code_short_key = """
import os
os.environ["ENVIRONMENT"] = "production"
os.environ["MULEGUARD_BIO_KEY"] = "short_16_bytes!"
try:
    from app.services.security import BIO_ENCRYPTION_KEY
    print("UNEXPECTED_SUCCESS")
except RuntimeError as e:
    if "CRITICAL SECURITY CONFIGURATION ERROR" in str(e):
        print("EXPECTED_FAIL_INVALID_LEN")
    else:
        print("OTHER_ERROR:", e)
"""
proc = subprocess.run(
    [sys.executable, "-c", code_short_key],
    capture_output=True,
    text=True,
    cwd="e:\\PROJECTS\\MULE GUARD",
    env=dict(os.environ, PYTHONPATH="e:\\PROJECTS\\MULE GUARD")
)
check("EXPECTED_FAIL_INVALID_LEN" in proc.stdout, "Startup correctly FAILS when MULEGUARD_BIO_KEY is not exactly 32 bytes")

# Valid 32-byte key test
code_valid_key = """
import os
os.environ["ENVIRONMENT"] = "production"
os.environ["MULEGUARD_BIO_KEY"] = "MuleGuard_Prod_Bio_Key_32_bytes!"
try:
    from app.services.security import BIO_ENCRYPTION_KEY
    if len(BIO_ENCRYPTION_KEY) == 32:
        print("VALID_KEY_LOADED")
except Exception as e:
    print("ERROR:", e)
"""
proc = subprocess.run(
    [sys.executable, "-c", code_valid_key],
    capture_output=True,
    text=True,
    cwd="e:\\PROJECTS\\MULE GUARD",
    env=dict(os.environ, PYTHONPATH="e:\\PROJECTS\\MULE GUARD")
)
check("VALID_KEY_LOADED" in proc.stdout, "Startup SUCCEEDS when valid 32-byte MULEGUARD_BIO_KEY is provided in production")


# 2.2 Spin up temporary production instance on port 8009 to test endpoints & headers
print("\n--- Sub-test 2.2: Production Endpoint Blocking & Security Headers ---")

prod_server_code = """
import os
os.environ["ENVIRONMENT"] = "production"
os.environ["MULEGUARD_BIO_KEY"] = "MuleGuard_Prod_Bio_Key_32_bytes!"
os.environ["ALLOWED_ORIGINS"] = "https://guard.muleguard.bank,https://compliance.muleguard.bank"

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8009, log_level="warning")
"""

prod_proc = subprocess.Popen(
    [sys.executable, "-c", prod_server_code],
    cwd="e:\\PROJECTS\\MULE GUARD",
    env=dict(os.environ, PYTHONPATH="e:\\PROJECTS\\MULE GUARD")
)

# Wait for server to be ready
time.sleep(3)
PROD_URL = "http://127.0.0.1:8009"

try:
    # Check health and production security headers
    prod_health_req = urllib.request.Request(f"{PROD_URL}/health")
    with urllib.request.urlopen(prod_health_req) as resp:
        check(resp.status == 200, "Production health check returns 200 OK")
        headers = dict(resp.headers)
        check(headers.get("x-content-type-options") == "nosniff", "Production X-Content-Type-Options: nosniff present")
        check(headers.get("x-frame-options") == "DENY", "Production X-Frame-Options: DENY present")
        check(headers.get("referrer-policy") == "strict-origin-when-cross-origin", "Production Referrer-Policy present")
        check("strict-transport-security" in headers, "Production HSTS header is present")
        check("max-age=31536000" in headers.get("strict-transport-security", ""), "Production HSTS specifies max-age=31536000")

    # Check /docs, /redoc, /openapi.json return 404 in production
    for path, name in [("/docs", "Swagger /docs"), ("/redoc", "ReDoc /redoc"), ("/openapi.json", "OpenAPI schema /openapi.json")]:
        try:
            urllib.request.urlopen(f"{PROD_URL}{path}")
            check(False, f"{name} should return 404 in production but returned 200")
        except urllib.error.HTTPError as he:
            check(he.code == 404, f"{name} returns 404 in production (blocked)")

    # Check demo endpoints return 404 in production
    demo_vec_req = urllib.request.Request(
        f"{PROD_URL}/api/v1/auth/demo-probe-vector",
        data=json.dumps({"employee_id": "MG-INV-001"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(demo_vec_req)
        check(False, "POST /demo-probe-vector should return 404 in production")
    except urllib.error.HTTPError as he:
        check(he.code == 404, "POST /api/v1/auth/demo-probe-vector returns 404 in production (blocked)")

    try:
        urllib.request.urlopen(f"{PROD_URL}/api/v1/auth/demo-sample-face")
        check(False, "GET /demo-sample-face should return 404 in production")
    except urllib.error.HTTPError as he:
        check(he.code == 404, "GET /api/v1/auth/demo-sample-face returns 404 in production (blocked)")

    # Test synthetic probe vector rejection in Stage 2 biometrics
    # First get a valid Stage 1 challenge
    s1_req = urllib.request.Request(
        f"{PROD_URL}/api/v1/auth/stage1-login",
        data=json.dumps({"employee_id": "MG-INV-001", "password": "Password@123"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(s1_req) as s1_resp:
        s1_data = json.loads(s1_resp.read().decode("utf-8"))
        challenge_token = s1_data.get("challenge", {}).get("challenge_token")
        check(s1_resp.status == 200, "Stage 1 login succeeds in production")

    # Send Stage 2 with synthetic probe_vector (must be rejected with HTTP 400)
    s2_synth_req = urllib.request.Request(
        f"{PROD_URL}/api/v1/auth/stage2-verify-face",
        data=json.dumps({"challenge_token": challenge_token, "probe_vector": [0.1] * 128}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(s2_synth_req)
        check(False, "Stage 2 with probe_vector should be rejected in production")
    except urllib.error.HTTPError as he:
        check(he.code == 400, f"Stage 2 with synthetic probe_vector rejected with HTTP 400 in production (got {he.code})")
        err_body = json.loads(he.read().decode("utf-8"))
        check("Synthetic probe vectors are prohibited in production" in err_body.get("detail", ""), "Clear rejection reason returned")

    # Check Production Cookie configuration
    from app.core.config import COOKIE_HTTPONLY, COOKIE_SAMESITE
    check(COOKIE_HTTPONLY is True, "Production cookie has HttpOnly=True")
    check(COOKIE_SAMESITE in ["lax", "strict"], f"Production cookie has SameSite={COOKIE_SAMESITE}")

finally:
    # Terminate the temporary production server
    prod_proc.terminate()
    prod_proc.wait()


# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "=" * 70)
print(f"PRODUCTION SECURITY REMEDIATION RESULTS: {passed} PASSED | {failed} FAILED")
print("=" * 70)

if failed > 0:
    sys.exit(1)
