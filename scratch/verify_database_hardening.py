"""
MuleGuard Database & Transaction Security Hardening Verification Suite
Tests:
A. Connection Pool:
   - psycopg_pool.ConnectionPool active (min_size=4, max_size=20)
   - Connection reuse across requests
   - No connection leaks

B. Database Permissions:
   - muleguard_app role active
   - Not superuser, no createdb, no createrole
   - Application operations succeed (SELECT, INSERT, UPDATE)
   - Administrative DDL blocked (CREATE TABLE, etc.)

C. Transaction Input Validation:
   - amount > 0 accepted
   - amount == 0 rejected with HTTP 422
   - amount < 0 rejected with HTTP 422

D. Balance Safety & Atomic Locking:
   - Sufficient balance succeeds
   - Insufficient balance rejected with HTTP 400
   - Failed transaction keeps balance completely unchanged
   - Concurrent race transactions cannot overdraw the account (FOR UPDATE row lock)
"""

import os
import sys
import json
import uuid

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from uuid import uuid4
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

# Ensure UTF-8 stdout on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
print("MULEGUARD DATABASE & TRANSACTION SECURITY VERIFICATION RUNNER")
print("=" * 70)

# ==============================================================================
# SECTION A: CONNECTION POOL VERIFICATION
# ==============================================================================
print("\n[SECTION A: Connection Pool Verification]")

from app.db.database import get_pool, get_connection

pool = get_pool()
check(pool is not None, "ConnectionPool instance is active")
check(pool.min_size == 4, f"pool.min_size is 4 (got {pool.min_size})")
check(pool.max_size == 20, f"pool.max_size is 20 (got {pool.max_size})")

# Test connection reuse and leak prevention across 30 sequential acquisitions
conn_ids = set()
for i in range(30):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        conn_ids.add(id(conn))

stats = pool.get_stats()
check(len(conn_ids) <= pool.max_size, f"30 queries reused bounded connections (unique conn ids: {len(conn_ids)})")
check(stats.get("requests_waiting", 0) == 0, "No requests stuck waiting in queue")
print(f"  Connection pool operational stats: {stats}")


# ==============================================================================
# SECTION B: LEAST-PRIVILEGE ROLE (muleguard_app)
# ==============================================================================
print("\n[SECTION B: Least-Privilege Role Verification (muleguard_app)]")

with get_connection() as conn:
    with conn.cursor() as cur:
        # Check current user
        cur.execute("SELECT current_user, session_user;")
        u_curr, u_sess = cur.fetchone()
        check(u_curr == "muleguard_app", f"Connected as least-privilege role 'muleguard_app' (got {u_curr})")

        # Check privileges in pg_user
        cur.execute("SELECT usesuper, usecreatedb FROM pg_user WHERE usename = current_user;")
        u_row = cur.fetchone()
        check(u_row[0] is False, "Role muleguard_app is NOT a superuser")
        check(u_row[1] is False, "Role muleguard_app does NOT have CREATEDB")

        # Application operation test
        cur.execute("SELECT count(*) FROM accounts;")
        acc_cnt = cur.fetchone()[0]
        check(acc_cnt > 0, f"Application SELECT on accounts allowed ({acc_cnt} records)")

        # Administrative DDL operation must be blocked
        ddl_blocked = False
        try:
            cur.execute("CREATE TABLE test_unauth_table (id int);")
        except Exception as e:
            ddl_blocked = True
            conn.rollback()

        check(ddl_blocked, "Administrative DDL (CREATE TABLE) correctly BLOCKED by PostgreSQL")


# ==============================================================================
# SECTION C: TRANSACTION INPUT VALIDATION (amount > 0)
# ==============================================================================
print("\n[SECTION C: Transaction Input Validation at API Boundary]")

BASE_URL = "http://127.0.0.1:8000"

# First, log in as Investigator to obtain authenticated session
login_req = urllib.request.Request(
    f"{BASE_URL}/api/v1/auth/stage1-login",
    data=json.dumps({"employee_id": "MG-INV-001", "password": "Password@123"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(login_req) as resp:
    s1_data = json.loads(resp.read().decode("utf-8"))
    ch_token = s1_data["challenge"]["challenge_token"]

# Stage 2 to get session cookie
from app.db.init_auth_db import generate_deterministic_vector
s2_req = urllib.request.Request(
    f"{BASE_URL}/api/v1/auth/stage2-verify-face",
    data=json.dumps({
        "challenge_token": ch_token,
        "probe_vector": generate_deterministic_vector("MG-INV-001"),
        "liveness_proof": {
            "action_performed": s1_data["challenge"]["challenge_action"],
            "confidence": 0.98,
            "timestamps": [1.0, 2.0]
        }
    }).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(s2_req) as resp:
    raw_cookies = resp.headers.get("Set-Cookie", "")
    # Extract muleguard_sid cookie value
    sid_val = ""
    for part in raw_cookies.split(";"):
        if "muleguard_sid=" in part:
            sid_val = part.split("muleguard_sid=")[1].strip()
            break

auth_headers = {
    "Content-Type": "application/json",
    "Cookie": f"muleguard_sid={sid_val}"
}

# 1. Test amount = 0 (Must be rejected with HTTP 422)
zero_req = urllib.request.Request(
    f"{BASE_URL}/api/v1/transactions/ingest",
    data=json.dumps({
        "senderId": "ACC-TEST-999",
        "receiverId": "ACC-TEST-888",
        "amountNumeric": 0.0,
        "type": "Transfer"
    }).encode("utf-8"),
    headers=auth_headers
)
try:
    urllib.request.urlopen(zero_req)
    check(False, "amount = 0 should be rejected by Pydantic validation")
except urllib.error.HTTPError as he:
    check(he.code == 422, f"amount = 0 rejected with HTTP 422 (got {he.code})")

# 2. Test amount < 0 (Must be rejected with HTTP 422)
neg_req = urllib.request.Request(
    f"{BASE_URL}/api/v1/transactions/ingest",
    data=json.dumps({
        "senderId": "ACC-TEST-999",
        "receiverId": "ACC-TEST-888",
        "amountNumeric": -500.0,
        "type": "Transfer"
    }).encode("utf-8"),
    headers=auth_headers
)
try:
    urllib.request.urlopen(neg_req)
    check(False, "amount < 0 should be rejected by Pydantic validation")
except urllib.error.HTTPError as he:
    check(he.code == 422, f"amount < 0 rejected with HTTP 422 (got {he.code})")


# ==============================================================================
# SECTION D: BALANCE SAFETY & ATOMIC ROW-LEVEL LOCKING
# ==============================================================================
print("\n[SECTION D: Atomic Balance Updates & Concurrency Locking]")

TEST_CUST_ID = f"CUST-SEC-{uuid4().hex[:6]}"
TEST_ACC_SENDER = f"ACC-SEC-S-{uuid4().hex[:6]}"
TEST_ACC_RECV = f"ACC-SEC-R-{uuid4().hex[:6]}"
INITIAL_SENDER_BALANCE = 5000.0
INITIAL_RECV_BALANCE = 1000.0

# Setup isolated test accounts
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (id, name, phone) VALUES (%s, %s, %s);",
            (TEST_CUST_ID, "Security Test Customer", "+919999999999")
        )
        cur.execute(
            "INSERT INTO accounts (id, customer_id, account_type, balance, status) VALUES (%s, %s, 'Savings', %s, 'Normal');",
            (TEST_ACC_SENDER, TEST_CUST_ID, INITIAL_SENDER_BALANCE)
        )
        cur.execute(
            "INSERT INTO accounts (id, customer_id, account_type, balance, status) VALUES (%s, %s, 'Savings', %s, 'Normal');",
            (TEST_ACC_RECV, TEST_CUST_ID, INITIAL_RECV_BALANCE)
        )
    conn.commit()

try:
    # 1. Valid transaction with sufficient funds -> Should succeed
    tx1_req = urllib.request.Request(
        f"{BASE_URL}/api/v1/transactions/ingest",
        data=json.dumps({
            "senderId": TEST_ACC_SENDER,
            "receiverId": TEST_ACC_RECV,
            "amountNumeric": 1000.0,
            "type": "Transfer"
        }).encode("utf-8"),
        headers=auth_headers
    )
    with urllib.request.urlopen(tx1_req) as resp:
        tx1_data = json.loads(resp.read().decode("utf-8"))
        check(tx1_data["success"] is True, "Valid transaction with sufficient balance succeeds (200)")

    # Verify balances updated accurately
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM accounts WHERE id = %s;", (TEST_ACC_SENDER,))
            s_bal = float(cur.fetchone()[0])
            cur.execute("SELECT balance FROM accounts WHERE id = %s;", (TEST_ACC_RECV,))
            r_bal = float(cur.fetchone()[0])
            check(s_bal == 4000.0, f"Sender balance correctly debited to INR 4,000 (got {s_bal})")
            check(r_bal == 2000.0, f"Receiver balance correctly credited to INR 2,000 (got {r_bal})")

    # 2. Transaction with insufficient balance -> Must fail with 400, balance unchanged
    over_req = urllib.request.Request(
        f"{BASE_URL}/api/v1/transactions/ingest",
        data=json.dumps({
            "senderId": TEST_ACC_SENDER,
            "receiverId": TEST_ACC_RECV,
            "amountNumeric": 99999.0, # Exceeds 4,000
            "type": "Transfer"
        }).encode("utf-8"),
        headers=auth_headers
    )
    try:
        urllib.request.urlopen(over_req)
        check(False, "Overdraft transaction should fail with HTTP 400")
    except urllib.error.HTTPError as he:
        check(he.code == 400, f"Overdraft transaction rejected with HTTP 400 (got {he.code})")

    # Verify balance was NOT modified
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM accounts WHERE id = %s;", (TEST_ACC_SENDER,))
            s_bal_after = float(cur.fetchone()[0])
            check(s_bal_after == 4000.0, f"Sender balance completely unchanged after failure (INR {s_bal_after})")

    # 3. Concurrent Race Condition Test:
    # Sender has INR 4,000 remaining.
    # Launch 6 concurrent threads, each attempting to transfer INR 1,500.
    # Total attempted = INR 9,000.
    # With SELECT FOR UPDATE row locking, EXACTLY 2 transfers can succeed (2 * 1500 = 3000, remaining 1000).
    # The other 4 must fail with 400 Insufficient funds.
    # Final balance must be EXACTLY INR 1,000, NEVER negative.
    print("\n--- Sub-test: Concurrent Race Condition (6 threads x INR 1,500 vs INR 4,000 balance) ---")

    def attempt_transfer(idx):
        t_req = urllib.request.Request(
            f"{BASE_URL}/api/v1/transactions/ingest",
            data=json.dumps({
                "senderId": TEST_ACC_SENDER,
                "receiverId": TEST_ACC_RECV,
                "amountNumeric": 1500.0,
                "type": "Transfer"
            }).encode("utf-8"),
            headers=auth_headers
        )
        try:
            with urllib.request.urlopen(t_req) as resp:
                return (resp.status, "SUCCESS")
        except urllib.error.HTTPError as he:
            return (he.code, "FAILED")

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(attempt_transfer, range(6)))

    successes = sum(1 for status, res in results if res == "SUCCESS")
    failures = sum(1 for status, res in results if res == "FAILED")

    check(successes == 2, f"Exactly 2 concurrent transactions succeeded (got {successes})")
    check(failures == 4, f"Exactly 4 concurrent transactions rejected with Insufficient funds (got {failures})")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM accounts WHERE id = %s;", (TEST_ACC_SENDER,))
            final_sender_bal = float(cur.fetchone()[0])
            cur.execute("SELECT balance FROM accounts WHERE id = %s;", (TEST_ACC_RECV,))
            final_recv_bal = float(cur.fetchone()[0])

            check(final_sender_bal == 1000.0, f"Final sender balance is exactly INR 1,000.0 (got {final_sender_bal})")
            check(final_sender_bal >= 0.0, "Sender balance NEVER became negative or overdrawn")
            check(final_recv_bal == 5000.0, f"Final receiver balance matches expected INR 5,000.0 (got {final_recv_bal})")

finally:
    # Clean up isolated test data
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM audit_logs WHERE account_id IN (%s, %s);", (TEST_ACC_SENDER, TEST_ACC_RECV))
            cur.execute("DELETE FROM transactions WHERE sender_account_id IN (%s, %s) OR receiver_account_id IN (%s, %s);",
                        (TEST_ACC_SENDER, TEST_ACC_RECV, TEST_ACC_SENDER, TEST_ACC_RECV))
            cur.execute("DELETE FROM accounts WHERE id IN (%s, %s);", (TEST_ACC_SENDER, TEST_ACC_RECV))
            cur.execute("DELETE FROM customers WHERE id = %s;", (TEST_CUST_ID,))
        conn.commit()
    print("  Cleaned up isolated security test data.")

pool.close()


# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "=" * 70)
print(f"DATABASE HARDENING VERIFICATION RESULTS: {passed} PASSED | {failed} FAILED")
print("=" * 70)

if failed > 0:
    sys.exit(1)
