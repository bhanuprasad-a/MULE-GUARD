import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
import json
import psycopg
from app.db.database import get_connection
from app.services.feature_engine import FEATURE_ORDER
from app.services.rule_engine import CANONICAL_RULES

print("=== MULEGUARD STEP 10: END-TO-END READ-ONLY AUDIT ===")

# 1. PostgreSQL Source-of-Truth Check
print("\n[1] Checking PostgreSQL Source of Truth...")
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_user, current_database();")
        user, db = cur.fetchone()
        print(f"  Connected DB: {db}, Current User: {user}")
        
        cur.execute("SELECT count(*) FROM accounts;")
        acc_cnt = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM transactions;")
        tx_cnt = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM alerts;")
        alert_cnt = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM cases;")
        case_cnt = cur.fetchone()[0]
        print(f"  PostgreSQL Counts: {acc_cnt} accounts, {tx_cnt} transactions, {alert_cnt} alerts, {case_cnt} cases")

# 2. ML Model & 26-Feature Integrity Check
print("\n[2] Checking ML Model & 26-Feature Integrity...")
model_path = Path("data/muleguard_postgres_model.json")
if model_path.exists():
    model_data = json.loads(model_path.read_text(encoding='utf-8'))
    tree_count = len(model_data.get('trees', []))
    features = model_data.get('features', [])
    print(f"  Model File: {model_path} exists")
    print(f"  Tree Count: {tree_count} (expected 80)")
    print(f"  Feature Count in Model: {len(features)} (expected 26)")
    print(f"  FEATURE_ORDER Count: {len(FEATURE_ORDER)} (expected 26)")
    matches = (features == FEATURE_ORDER)
    print(f"  Exact Feature Ordering Match: {matches}")
else:
    print(f"  ERROR: Model file not found at {model_path}")

# 3. Canonical Detection Rules Check
print("\n[3] Checking Canonical Detection Rules...")
print(f"  Active Rules Count: {len(CANONICAL_RULES)} (expected 6)")
rule_ids = [r['id'] for r in CANONICAL_RULES]
print(f"  Active Rule IDs: {rule_ids}")
expected_rules = ['R-VEL-1', 'R-AGG-1', 'R-DIST-1', 'R-HOLD-1', 'R-CIRC-1', 'R-DORM-1']
print(f"  Matches Expected 6 Rules: {rule_ids == expected_rules}")

# 4. Frontend Production HTML Check
print("\n[4] Checking Production HTML Pages for Legacy Dependencies...")
html_files = list(Path('frontend').rglob('*.html'))
unexplained_refs = []
for html in html_files:
    txt = html.read_text(encoding='utf-8', errors='ignore')
    # search for MuleGuardStore banking calls
    bad_calls = re.findall(r'MuleGuardStore\.(?:getAccounts|getTransactions|getAlerts|getCases|getDecisions|getWatchlist|getAuditLogs|getNetworks|predictAccountRisk)', txt)
    if bad_calls:
        unexplained_refs.append((str(html), bad_calls))

if not unexplained_refs:
    print("  Zero unexplained MuleGuardStore banking calls across all HTML files! (PASS)")
else:
    print(f"  Found legacy calls: {unexplained_refs}")

print("\n[5] End-to-End Audit Script Complete.")
