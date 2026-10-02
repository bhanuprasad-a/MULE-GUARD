"""
Complete End-to-End Verification Test for MuleGuard
Tests real HTTP server startup, routing, login, dashboards, network intelligence, and PostgreSQL APIs.
"""

import sys
import time
import socket
import urllib.request
import urllib.error
import json
import subprocess

PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"

print("=== STARTING REAL-TIME END-TO-END FLOW VERIFICATION ===")

# Start server using run.py in a subprocess
proc = subprocess.Popen(
    [sys.executable, "run.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait for server to become responsive
started = False
for attempt in range(40):
    time.sleep(0.3)
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1.0) as res:
            if res.status == 200:
                started = True
                print(f"[PASS] Server is listening and healthy at {BASE_URL} (attempt {attempt+1})")
                break
    except Exception:
        pass

if not started:
    print("[FAIL] Server failed to start within timeout.")
    proc.terminate()
    sys.exit(1)

def check_endpoint(path, expected_status=200, check_fn=None):
    url = f"{BASE_URL}{path}"
    # Custom opener to handle redirects without automatic follow if checking redirect
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        res = opener.open(url, timeout=3.0)
        status = res.status
        body = res.read()
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read()
    except Exception as ex:
        print(f"[FAIL] {path:55} -> Connection Error: {ex}")
        return False

    status_ok = (status == expected_status)
    extra_ok = True
    extra_msg = ""
    if check_fn:
        extra_ok, extra_msg = check_fn(body)

    if status_ok and extra_ok:
        print(f"[PASS] {path:55} -> HTTP {status} {extra_msg}")
        return True
    else:
        print(f"[FAIL] {path:55} -> HTTP {status} (Expected {expected_status}) {extra_msg}")
        return False

results = []

# 1. Root redirect
results.append(check_endpoint("/", 307))

# 2. Login pages (both root and /frontend paths)
results.append(check_endpoint("/frontend/login.html", 200, lambda b: (b"MuleGuard - Secure Sign In" in b, "[Page Title verified]")))
results.append(check_endpoint("/login.html", 200, lambda b: (b"MuleGuard - Secure Sign In" in b, "[Root-mounted login verified]")))

# 3. Assets & Styles
results.append(check_endpoint("/frontend/style.css", 200))
results.append(check_endpoint("/frontend/scripts/auth-guard.js", 200))
results.append(check_endpoint("/frontend/scripts/api.js", 200))
results.append(check_endpoint("/assets/MULEGUARD_LOGO_W&G.png", 200))

# 4. Compliance Dashboard & Navigation
results.append(check_endpoint("/frontend/bank/compliance/dashboard.html", 200, lambda b: (b"Compliance Control Center" in b, "[Heading verified]")))
results.append(check_endpoint("/frontend/bank/compliance/network-intelligence.html", 200, lambda b: (b"Network Intelligence" in b, "[Heading verified]")))
results.append(check_endpoint("/frontend/bank/compliance/fraud_networks.html", 200, lambda b: (b"Fraud Networks" in b, "[Heading verified]")))

# 5. Investigator Dashboard & Navigation
results.append(check_endpoint("/frontend/bank/investigator/dashboard.html", 200, lambda b: (b"MuleGuard Command Center" in b or b"Dashboard" in b, "[Content verified]")))
results.append(check_endpoint("/frontend/bank/investigator/network-intelligence.html", 200, lambda b: (b"Network Intelligence" in b, "[Heading verified]")))
results.append(check_endpoint("/frontend/bank/investigator/fraud_networks.html", 200, lambda b: (b"Fraud Networks" in b, "[Heading verified]")))

# 6. Backend PostgreSQL APIs
def check_networks_json(b):
    try:
        data = json.loads(b)
        count = len(data)
        if count > 0 and "id" in data[0] and "score" in data[0]:
            return True, f"[{count} live PostgreSQL networks received]"
        return False, f"[Invalid payload format: {data[:1]}]"
    except Exception as e:
        return False, f"[JSON parse error: {e}]"

results.append(check_endpoint("/api/v1/networks", 200, check_networks_json))
results.append(check_endpoint("/api/v1/accounts", 200, lambda b: (len(json.loads(b)) > 0, f"[{len(json.loads(b))} accounts]")))
results.append(check_endpoint("/api/v1/alerts", 200, lambda b: (isinstance(json.loads(b), list), "[Alerts received]")))
results.append(check_endpoint("/api/v1/cases", 200, lambda b: (isinstance(json.loads(b), list), "[Cases received]")))
results.append(check_endpoint("/api/v1/kpis", 200, lambda b: ("total_accounts" in json.loads(b), "[Live KPIs verified]")))

# Cleanly terminate server
proc.terminate()
try:
    proc.wait(timeout=2.0)
except Exception:
    proc.kill()

print("=" * 68)
total_tests = len(results)
passed_tests = sum(results)
print(f"SUMMARY: {passed_tests}/{total_tests} END-TO-END FLOW CHECKS PASSED")
print("=" * 68)

if passed_tests == total_tests:
    print("ALL CHECKS PASSED!")
    sys.exit(0)
else:
    print(f"FAILED {total_tests - passed_tests} CHECKS")
    sys.exit(1)
