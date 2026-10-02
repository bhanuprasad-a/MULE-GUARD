from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.api.auth import require_role


router = APIRouter(
    prefix="/api/v1",
    tags=["Application"],
)


# =========================
# WATCHLISTS
# =========================

@router.get("/watchlists", dependencies=[Depends(require_role(["bank_investigator", "bank_compliance", "internal_team"]))])
def get_watchlists():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    w.id,
                    w.account_id,
                    w.reason,
                    w.status,
                    w.created_at,
                    c.name AS customer_name,
                    a.account_type,
                    a.balance
                FROM watchlists w
                LEFT JOIN accounts a ON w.account_id = a.id
                LEFT JOIN customers c ON a.customer_id = c.id
                ORDER BY w.created_at DESC
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "account_id": r[1],
            "accountId": r[1],
            "reason": r[2],
            "status": r[3],
            "created_at": r[4],
            "addedAt": r[4],
            "customer_name": r[5] or r[1],
            "accountName": r[5] or r[1],
            "entity": r[5] or r[1],
            "account_type": r[6] or "Savings",
            "balance": float(r[7]) if r[7] is not None else 0.0,
            "priority": "High" if (r[7] and r[7] > 100000) else "Medium",
        }
        for r in rows
    ]


@router.post("/watchlists/{account_id}", dependencies=[Depends(require_role(["bank_investigator", "bank_compliance", "internal_team"]))])
def add_to_watchlist(account_id: str, reason: str = "Suspicious activity"):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT id FROM accounts WHERE id = %s",
                (account_id,),
            )

            if not cur.fetchone():
                raise HTTPException(404, "Account not found")

            watchlist_id = f"WL-{uuid4().hex[:12].upper()}"

            cur.execute(
                """
                INSERT INTO watchlists (
                    id,
                    account_id,
                    reason
                )
                VALUES (%s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    watchlist_id,
                    account_id,
                    reason,
                ),
            )

            row = cur.fetchone()

    return {
        "id": row[0],
        "account_id": account_id,
        "reason": reason,
        "status": "Active",
        "created_at": row[1],
    }


# =========================
# DECISIONS
# =========================

@router.get("/decisions", dependencies=[Depends(require_role(["bank_compliance"]))])
def get_decisions():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    d.id,
                    d.account_id,
                    d.alert_id,
                    d.decision,
                    d.reason,
                    d.created_at,
                    c.name AS customer_name,
                    a.account_type,
                    a.balance
                FROM decisions d
                LEFT JOIN accounts a ON d.account_id = a.id
                LEFT JOIN customers c ON a.customer_id = c.id
                ORDER BY d.created_at DESC
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "account_id": r[1],
            "accountId": r[1],
            "alert_id": r[2],
            "decision": r[3],
            "reason": r[4],
            "created_at": r[5],
            "customer_name": r[6] or r[1],
            "accountName": r[6] or r[1],
            "entity": r[6] or r[1],
            "account_type": r[7] or "Savings",
            "balance": float(r[8]) if r[8] is not None else 0.0,
        }
        for r in rows
    ]


@router.post("/decisions/{account_id}", dependencies=[Depends(require_role(["bank_compliance"]))])
def create_decision(
    account_id: str,
    decision: str,
    reason: str = "",
    alert_id: str | None = None,
):
    allowed = {"Monitor", "Clear", "Block", "Escalate"}

    if decision not in allowed:
        raise HTTPException(
            400,
            f"Decision must be one of: {', '.join(sorted(allowed))}",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT id FROM accounts WHERE id = %s",
                (account_id,),
            )

            if not cur.fetchone():
                raise HTTPException(404, "Account not found")

            decision_id = f"DEC-{uuid4().hex[:12].upper()}"

            cur.execute(
                """
                INSERT INTO decisions (
                    id,
                    account_id,
                    alert_id,
                    decision,
                    reason
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    decision_id,
                    account_id,
                    alert_id,
                    decision,
                    reason,
                ),
            )

            row = cur.fetchone()

            cur.execute(
                """
                INSERT INTO audit_logs (
                    action,
                    entity_type,
                    entity_id,
                    account_id,
                    details
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "DECISION_CREATED",
                    "decision",
                    decision_id,
                    account_id,
                    Jsonb({
                        "decision": decision,
                        "reason": reason,
                        "alert_id": alert_id,
                    }),
                ),
            )

    return {
        "id": row[0],
        "account_id": account_id,
        "alert_id": alert_id,
        "decision": decision,
        "reason": reason,
        "created_at": row[1],
    }


# =========================
# RULES
# =========================

@router.get("/rules", dependencies=[Depends(require_role(["internal_team"]))])
def get_rules():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    enabled,
                    created_at
                FROM rules
                ORDER BY id
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "enabled": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]


from app.services.network_engine import compute_network_intelligence


# =========================
# NETWORKS
# =========================

@router.get("/networks", dependencies=[Depends(require_role(["bank_investigator", "bank_compliance"]))])
def get_networks():
    networks_dict = compute_network_intelligence()
    return list(networks_dict.values())



# =========================
# KPI
# =========================

@router.get("/kpis", dependencies=[Depends(require_role(["bank_investigator", "bank_compliance", "internal_team"]))])
def get_kpis():
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT COUNT(*) FROM accounts")
            total_accounts = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM accounts
                WHERE status IN (
                    'Flagged',
                    'Critical',
                    'Under Review',
                    'Blocked'
                )
                """
            )
            suspicious_accounts = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM transactions"
            )
            total_transactions = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM alerts
                WHERE status = 'Open'
                """
            )
            open_alerts = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM cases
                WHERE status != 'Resolved'
                """
            )
            active_cases = cur.fetchone()[0]

    return {
        "total_accounts": total_accounts,
        "suspicious_accounts": suspicious_accounts,
        "high_risk_accounts": 18,
        "total_transactions": total_transactions,
        "open_alerts": open_alerts,
        "active_cases": active_cases,
    }