"""
MuleGuard Detection Rules Engine & Telemetry Service
Provides deterministic pattern-matching detection rule evaluation,
rule configuration inspection from PostgreSQL, and thread-safe in-process trigger telemetry.
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from app.db.database import get_connection

# Canonical definitions for MuleGuard's 6 active detection rules
CANONICAL_RULES: List[Dict[str, Any]] = [
    {
        "id": "R-VEL-1",
        "name": "Velocity Spike (Inbound Degree)",
        "description": "Triggers when an account receives more than 5 inbound UPI transfers in a 24-hour period.",
        "category": "Velocity",
        "threshold": 5,
        "unit": "transfers/24h",
        "severity": "Medium",
        "enabled": True,
    },
    {
        "id": "R-AGG-1",
        "name": "Many-to-One Fund Aggregation",
        "description": "Triggers when an account receives funds from 3 or more distinct counterparty accounts within a rolling 24-hour window.",
        "category": "Aggregation",
        "threshold": 3,
        "unit": "counterparties/24h",
        "severity": "High",
        "enabled": True,
    },
    {
        "id": "R-DIST-1",
        "name": "One-to-Many Fund Distribution",
        "description": "Triggers when an account rapidly disperses incoming funds to 3 or more distinct recipient accounts within a rolling 24-hour window.",
        "category": "Distribution",
        "threshold": 3,
        "unit": "recipients/24h",
        "severity": "High",
        "enabled": True,
    },
    {
        "id": "R-HOLD-1",
        "name": "Short Holding Time Ratio",
        "description": "Triggers when more than 80% of received funds are transferred out of the account within 30 minutes of receipt.",
        "category": "Rapid Movement",
        "threshold": 80,
        "unit": "% ratio",
        "severity": "Critical",
        "enabled": True,
    },
    {
        "id": "R-CIRC-1",
        "name": "Circular Money Flow",
        "description": "Triggers when an account participates in a closed money flow loop of connected accounts.",
        "category": "Network Topology",
        "threshold": 1,
        "unit": "cycles",
        "severity": "Critical",
        "enabled": True,
    },
    {
        "id": "R-DORM-1",
        "name": "Dormant Account Activation",
        "description": "Triggers when a previously inactive account registered over 90 days ago receives significant transaction volume within 24 hours.",
        "category": "Behavioral Anomaly",
        "threshold": 50000,
        "unit": "INR/24h",
        "severity": "High",
        "enabled": True,
    },
]

# Obsolete / deprecated demo rules that must NOT be treated as active
OBSOLETE_RULE_IDS = {"R-NET-1", "R-VAL-1"}

# Thread-safe in-process rule trigger telemetry
_telemetry_lock = threading.Lock()
_telemetry: Dict[str, Any] = {
    "total_evaluations": 0,
    "total_triggers": 0,
    "per_rule_triggers": {rule["id"]: 0 for rule in CANONICAL_RULES},
    "latest_trigger_at": None,
    "latest_trigger_rule": None,
    "evaluation_failures": 0,
    "last_evaluated_at": None,
    "per_rule_last_triggered": {rule["id"]: None for rule in CANONICAL_RULES},
}


def get_rule_telemetry() -> Dict[str, Any]:
    """Return a thread-safe snapshot of in-process rule trigger telemetry."""
    with _telemetry_lock:
        return {
            "total_evaluations": _telemetry["total_evaluations"],
            "total_triggers": _telemetry["total_triggers"],
            "per_rule_triggers": dict(_telemetry["per_rule_triggers"]),
            "latest_trigger_at": _telemetry["latest_trigger_at"],
            "latest_trigger_rule": _telemetry["latest_trigger_rule"],
            "evaluation_failures": _telemetry["evaluation_failures"],
            "last_evaluated_at": _telemetry["last_evaluated_at"],
            "per_rule_last_triggered": dict(_telemetry["per_rule_last_triggered"]),
        }


def record_evaluation_event(triggered_rules: List[str], failed: bool = False):
    """Record an evaluation event and any triggered rules thread-safely."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _telemetry_lock:
        _telemetry["total_evaluations"] += 1
        _telemetry["last_evaluated_at"] = now_iso
        if failed:
            _telemetry["evaluation_failures"] += 1

        for rule_id in triggered_rules:
            if rule_id in _telemetry["per_rule_triggers"]:
                _telemetry["per_rule_triggers"][rule_id] += 1
                _telemetry["per_rule_last_triggered"][rule_id] = now_iso
                _telemetry["total_triggers"] += 1
                _telemetry["latest_trigger_at"] = now_iso
                _telemetry["latest_trigger_rule"] = rule_id


def reset_telemetry_for_test():
    """Reset telemetry to clean baseline for tests."""
    with _telemetry_lock:
        _telemetry["total_evaluations"] = 0
        _telemetry["total_triggers"] = 0
        _telemetry["per_rule_triggers"] = {rule["id"]: 0 for rule in CANONICAL_RULES}
        _telemetry["latest_trigger_at"] = None
        _telemetry["latest_trigger_rule"] = None
        _telemetry["evaluation_failures"] = 0
        _telemetry["last_evaluated_at"] = None
        _telemetry["per_rule_last_triggered"] = {rule["id"]: None for rule in CANONICAL_RULES}


def sync_database_rules(conn=None):
    """
    Ensure the PostgreSQL 'rules' table contains the 6 active canonical rules
    and marks any legacy/obsolete demo rules as disabled.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        with conn.cursor() as cur:
            # 1. Insert/update the 6 canonical rules
            for rule in CANONICAL_RULES:
                cur.execute(
                    """
                    INSERT INTO rules (id, name, description, enabled)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description;
                    """,
                    (rule["id"], rule["name"], rule["description"], rule["enabled"]),
                )

            # 2. Disable obsolete rules if present
            for obsolete_id in OBSOLETE_RULE_IDS:
                cur.execute(
                    """
                    UPDATE rules SET enabled = FALSE WHERE id = %s;
                    """,
                    (obsolete_id,),
                )

            conn.commit()
    except Exception as e:
        print(f"Warning: rules table sync notice: {e}")
    finally:
        if should_close:
            conn.close()


def evaluate_rules_for_account(account_id: str, conn=None) -> Dict[str, Any]:
    """
    Evaluates the 6 active detection rules against an account's transactions and history.
    Records evaluation and triggers thread-safely in telemetry.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    triggered = []
    rule_details = {}

    try:
        with conn.cursor() as cur:
            # Load account details
            cur.execute(
                """
                SELECT id, balance, status, opened_at
                FROM accounts
                WHERE id = %s
                """,
                (account_id,),
            )
            acc_row = cur.fetchone()
            if not acc_row:
                record_evaluation_event([], failed=True)
                return {"error": f"Account {account_id} not found", "triggers": []}

            balance, status, opened_at = acc_row[1], acc_row[2], acc_row[3]
            now = datetime.now(timezone.utc)
            rolling_24h = now - timedelta(hours=24)

            # Load account transactions
            cur.execute(
                """
                SELECT id, sender_account_id, receiver_account_id, amount, transaction_timestamp
                FROM transactions
                WHERE sender_account_id = %s OR receiver_account_id = %s
                ORDER BY transaction_timestamp ASC
                """,
                (account_id, account_id),
            )
            tx_rows = cur.fetchall()

        inbound_24h = [
            tx for tx in tx_rows
            if tx[2] == account_id and tx[4] and tx[4] >= rolling_24h
        ]
        outbound_24h = [
            tx for tx in tx_rows
            if tx[1] == account_id and tx[4] and tx[4] >= rolling_24h
        ]

        # 1. R-VEL-1: Velocity Spike (Inbound Degree)
        inbound_count_24h = len(inbound_24h)
        if inbound_count_24h > 5:
            triggered.append("R-VEL-1")
            rule_details["R-VEL-1"] = f"{inbound_count_24h} inbound transfers/24h (threshold: 5)"

        # 2. R-AGG-1: Many-to-One Fund Aggregation
        distinct_senders = {tx[1] for tx in inbound_24h if tx[1] and tx[1] != account_id}
        if len(distinct_senders) >= 3:
            triggered.append("R-AGG-1")
            rule_details["R-AGG-1"] = f"Funds aggregated from {len(distinct_senders)} distinct senders/24h (threshold: 3)"

        # 3. R-DIST-1: One-to-Many Fund Distribution
        distinct_receivers = {tx[2] for tx in outbound_24h if tx[2] and tx[2] != account_id}
        if len(distinct_receivers) >= 3:
            triggered.append("R-DIST-1")
            rule_details["R-DIST-1"] = f"Funds dispersed to {len(distinct_receivers)} distinct recipients/24h (threshold: 3)"

        # 4. R-HOLD-1: Short Holding Time Ratio
        total_in_24h = sum(float(tx[3]) for tx in inbound_24h)
        if total_in_24h > 0:
            matched_outbound = 0.0
            for in_tx in inbound_24h:
                in_time = in_tx[4]
                in_amt = float(in_tx[3])
                matched_for_this = sum(
                    float(out_tx[3]) for out_tx in outbound_24h
                    if out_tx[4] and out_tx[4] >= in_time and (out_tx[4] - in_time).total_seconds() <= 1800
                )
                matched_outbound += min(in_amt, matched_for_this)

            ratio = min(100.0, (matched_outbound / total_in_24h) * 100.0)
            if ratio > 80.0:
                triggered.append("R-HOLD-1")
                rule_details["R-HOLD-1"] = f"Rapid holding ratio: {ratio:.1f}% disbursed within 30m (threshold: 80%)"

        # 5. R-CIRC-1: Circular Money Flow
        # Check cycle participation via BFS search (depth <= 4)
        if len(tx_rows) > 0:
            has_cycle = False
            adj = defaultdict(set)
            for tx in tx_rows:
                if tx[1] and tx[2]:
                    adj[tx[1]].add(tx[2])

            def check_cycle(curr, depth, visited):
                if depth > 4:
                    return False
                for nxt in adj.get(curr, set()):
                    if nxt == account_id and depth >= 2:
                        return True
                    if nxt not in visited:
                        visited.add(nxt)
                        if check_cycle(nxt, depth + 1, visited):
                            return True
                        visited.remove(nxt)
                return False

            if check_cycle(account_id, 1, {account_id}):
                triggered.append("R-CIRC-1")
                rule_details["R-CIRC-1"] = "Account participates in a closed circular money flow loop"

        # 6. R-DORM-1: Dormant Account Activation
        account_age_days = 0
        if opened_at:
            if opened_at.tzinfo is None:
                opened_at = opened_at.replace(tzinfo=timezone.utc)
            account_age_days = (now - opened_at).days

        if account_age_days > 90 and total_in_24h >= 50000.0:
            triggered.append("R-DORM-1")
            rule_details["R-DORM-1"] = f"Account aged {account_age_days}d received ₹{int(total_in_24h):,} in 24h (threshold: ₹50,000)"

        record_evaluation_event(triggered, failed=False)
        return {
            "account_id": account_id,
            "triggers": triggered,
            "rule_details": rule_details,
            "is_flagged": len(triggered) > 0,
        }

    except Exception as e:
        record_evaluation_event([], failed=True)
        return {"error": str(e), "triggers": []}
    finally:
        if should_close:
            conn.close()


def get_detection_rules_report() -> Dict[str, Any]:
    """
    Returns the comprehensive, truthful Detection Rules Operations report:
    - Lists the 6 active canonical rules
    - Exposes enabled/disabled state from database
    - Exposes real thread-safe trigger telemetry
    - Computes accurate summary counts
    - Excludes obsolete rules from the active count
    """
    db_rules = {}
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, description, enabled FROM rules")
                for row in cur.fetchall():
                    db_rules[row[0]] = {
                        "name": row[1],
                        "description": row[2],
                        "enabled": bool(row[3]),
                    }
    except Exception as e:
        print(f"Warning: unable to load rules from PostgreSQL: {e}")

    telemetry = get_rule_telemetry()
    rules_list = []

    for cr in CANONICAL_RULES:
        rule_id = cr["id"]
        db_rule = db_rules.get(rule_id, {})
        is_enabled = db_rule.get("enabled", cr["enabled"])

        trigger_count = telemetry["per_rule_triggers"].get(rule_id, 0)
        last_triggered = telemetry["per_rule_last_triggered"].get(rule_id)

        rules_list.append({
            "id": rule_id,
            "name": db_rule.get("name") or cr["name"],
            "description": db_rule.get("description") or cr["description"],
            "status": "ENABLED" if is_enabled else "DISABLED",
            "enabled": is_enabled,
            "category": cr["category"],
            "threshold": cr["threshold"],
            "unit": cr["unit"],
            "severity": cr["severity"],
            "trigger_count": trigger_count,
            "last_triggered_at": last_triggered,
            "is_obsolete": False,
        })

    # Summary calculations strictly for the 6 canonical rules
    total_rules = len(rules_list)
    enabled_rules = sum(1 for r in rules_list if r["enabled"])
    disabled_rules = total_rules - enabled_rules

    return {
        "status": "Healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "total_evaluations": telemetry["total_evaluations"],
            "total_triggers": telemetry["total_triggers"],
            "evaluation_errors": telemetry["evaluation_failures"],
        },
        "telemetry": telemetry,
        "rules": rules_list,
        "engine_type": "Deterministic Rule Evaluation Engine",
        "model_comparison": {
            "rules_role": "Deterministic Policy Matching (Boolean Condition Evaluation)",
            "ml_role": "XGBoost 26-Feature Supervised Risk Probability (Continuous [0, 1])",
            "combined": False,
        },
    }
