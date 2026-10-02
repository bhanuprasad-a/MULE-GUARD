"""
Exports authoritative PostgreSQL data into data/synthetic_db.json and frontend/scripts/synthetic_db_expanded.js.
Ensures complete consistency across the entire repository while keeping PostgreSQL as the primary source of truth.
"""

import sys, os, json
from datetime import datetime, timezone

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_DIR)

from app.db.database import get_connection

def export_db():
    print("[Export] Reading authoritative data from PostgreSQL...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Accounts + Customers
            cur.execute("""
                SELECT 
                    a.id, c.name, a.account_type, a.balance, a.status, 
                    a.opened_at, c.phone, c.device_fingerprint, c.ip_address, c.address
                FROM accounts a
                JOIN customers c ON c.id = a.customer_id
                ORDER BY a.id;
            """)
            acc_rows = cur.fetchall()

            # 2. Transactions
            cur.execute("""
                SELECT 
                    id, sender_account_id, receiver_account_id, amount, 
                    transaction_type, status, transaction_timestamp, origin, destination
                FROM transactions
                ORDER BY transaction_timestamp;
            """)
            tx_rows = cur.fetchall()

            # 3. Alerts
            cur.execute("""
                SELECT id, account_id, risk_score, risk_probability, prediction, severity, status, created_at
                FROM alerts
                ORDER BY created_at;
            """)
            alt_rows = cur.fetchall()

            # 4. Cases
            cur.execute("""
                SELECT id, account_id, alert_id, title, status, priority, created_at, updated_at
                FROM cases
                ORDER BY created_at;
            """)
            case_rows = cur.fetchall()

    accounts_dict = {}
    now = datetime.now(timezone.utc)
    for r in acc_rows:
        acc_id = r[0]
        name = r[1]
        acc_type = r[2]
        balance = float(r[3])
        status = r[4]
        opened_at = r[5].strftime("%Y-%m-%d") if r[5] else "2024-01-01"
        phone = r[6]
        device = r[7]
        ip = str(r[8]) if r[8] else "192.168.1.1"
        address = r[9]

        risk_score = 92 if status in ("Critical", "Flagged") else (75 if status == "Under Review" else 20)

        accounts_dict[acc_id] = {
            "id": acc_id,
            "name": name,
            "type": acc_type,
            "balance": balance,
            "riskScore": risk_score,
            "status": status,
            "created": opened_at,
            "phone": phone,
            "device": device,
            "ip": ip,
            "address": address
        }

    transactions_list = []
    for r in tx_rows:
        tx_id = r[0]
        sender_id = r[1]
        receiver_id = r[2]
        amount = float(r[3])
        tx_type = r[4]
        status = r[5]
        ts = r[6]
        origin = r[7] or "India"
        destination = r[8] or "India"

        # Calculate relative time
        diff = now - ts
        diff_mins = max(1, int(diff.total_seconds() // 60))
        if diff_mins < 60:
            rel_time = f"{diff_mins} min ago"
        elif diff_mins < 1440:
            rel_time = f"{diff_mins // 60} hrs ago"
        else:
            rel_time = f"{diff_mins // 1440} days ago"

        transactions_list.append({
            "id": tx_id,
            "senderId": sender_id,
            "receiverId": receiver_id,
            "amountNumeric": amount,
            "value": f"₹{amount:,.2f}".rstrip('0').rstrip('.'),
            "type": tx_type,
            "status": status,
            "score": 50,
            "time": rel_time,
            "isoTimestamp": ts.isoformat(),
            "origin": origin,
            "destination": destination,
            "summary": f"{tx_type} of ₹{amount:,.0f} from {sender_id} to {receiver_id}"
        })

    alerts_list = []
    for r in alt_rows:
        alerts_list.append({
            "id": r[0],
            "accountId": r[1],
            "riskScore": float(r[2]),
            "riskProbability": float(r[3]),
            "prediction": r[4],
            "severity": r[5],
            "status": r[6],
            "createdTime": "Recent"
        })

    cases_list = []
    for r in case_rows:
        cases_list.append({
            "id": r[0],
            "primaryEntityId": r[1],
            "alertId": r[2],
            "title": r[3],
            "status": r[4],
            "priority": r[5],
            "createdTime": "Recent",
            "lastUpdated": "Recent",
            "activity": [],
            "notes": ""
        })

    rules_list = [
        { "id": "R-VEL-1", "name": "Velocity Spike (Inbound Degree)", "threshold": 5, "unit": "transfers/24h", "description": "Triggers when an account receives more than the threshold of inbound UPI transfers in a 24-hour period.", "active": True },
        { "id": "R-HOLD-1", "name": "Short Holding Time Ratio", "threshold": 80, "unit": "% ratio", "description": "Triggers when more than the threshold of received funds are transferred out of the account within 30 minutes.", "active": True },
        { "id": "R-NET-1", "name": "Suspicious Component Connection", "threshold": 1, "unit": "hops", "description": "Triggers when a node has direct connection (shared device/IP/phone) to previously blocked/flagged fraud nodes.", "active": True },
        { "id": "R-VAL-1", "name": "High-Value Shell Transfer", "threshold": 100000, "unit": "INR", "description": "Triggers on a transfer exceeding threshold from/to newly registered corporate shell entities.", "active": True },
        { "id": "R-CIRC-1", "name": "Circular Money Flow", "threshold": 1, "unit": "cycles", "description": "Triggers when an account participates in a closed money flow loop of connected accounts.", "active": True },
        { "id": "R-DORM-1", "name": "Dormant Account Activation", "threshold": 50000, "unit": "INR/24h", "description": "Triggers when a previously inactive/dormant account receives significant transaction volume within 24 hours.", "active": True }
    ]

    seed_data = {
        "rules": rules_list,
        "accounts": accounts_dict,
        "transactions": transactions_list,
        "alerts": alerts_list,
        "cases": cases_list,
        "auditLogs": [],
        "networks": {},
        "watchlists": {}
    }

    # Write data/synthetic_db.json
    json_path = os.path.join(PROJECT_DIR, "data", "synthetic_db.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, indent=2)
    print(f"[Export] Saved {json_path}")

    # Write frontend/scripts/synthetic_db_expanded.js
    js_path = os.path.join(PROJECT_DIR, "frontend", "scripts", "synthetic_db_expanded.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("// Automatically generated expanded synthetic database seed from PostgreSQL\n")
        f.write("window.MuleGuardExpandedDB = ")
        json.dump(seed_data, f, indent=2)
        f.write(";\n")
    print(f"[Export] Saved {js_path}")

if __name__ == "__main__":
    export_db()
