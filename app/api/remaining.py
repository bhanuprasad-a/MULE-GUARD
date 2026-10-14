from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
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
def get_watchlists(
    limit: int = Query(default=100, ge=1, le=500, description="Max watchlists to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    search: Optional[str] = Query(default=None, description="Search by account ID, customer name, or reason"),
    status: Optional[str] = Query(default=None, description="Filter by status (Active, Removed)"),
):
    query = """
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
        WHERE 1=1
    """
    params = []

    if status and status.upper() != "ALL":
        query += " AND w.status = %s"
        params.append(status)

    if search:
        query += " AND (w.account_id ILIKE %s OR c.name ILIKE %s OR w.reason ILIKE %s)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])

    query += " ORDER BY w.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
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


@router.post("/watchlists/{account_id}")
def add_to_watchlist(
    account_id: str = Path(..., max_length=64, description="Target account ID"),
    reason: str = Query(default="Suspicious activity", max_length=256, description="Watchlist reason"),
    payload: Optional[dict] = Body(default=None),
    current_user: dict = Depends(require_role(["bank_investigator", "bank_compliance", "internal_team"])),
):
    if payload and isinstance(payload, dict) and payload.get("reason"):
        reason = str(payload["reason"])[:256]
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
                    "WATCHLIST_ADDED",
                    "watchlist",
                    watchlist_id,
                    account_id,
                    Jsonb({
                        "reason": reason,
                        "status": "Active",
                        "actor": current_user.get("employee_id") or "SYSTEM",
                    }),
                ),
            )

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
def get_decisions(
    limit: int = Query(default=100, ge=1, le=500, description="Max decisions to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
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
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
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
    account_id: str = Path(..., max_length=64, description="Target account ID"),
    decision: str = Query(..., max_length=32, description="Decision type"),
    reason: str = Query(default="", max_length=256, description="Decision rationale"),
    alert_id: str | None = Query(default=None, max_length=64, description="Optional associated alert ID"),
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

@router.get(
    "/rules",
    dependencies=[Depends(require_role(["internal_team"]))],
    deprecated=True,
    summary="[DEPRECATED] Query raw database rules table (Canonical: /api/v1/internal/detection-rules)",
)
def get_rules(
    limit: int = Query(default=50, ge=1, le=100, description="Max rules to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    """
    LEGACY ENDPOINT: Returns un-reconciled raw rows from the 'rules' table.
    Maintained for test and backwards-compatibility.
    Canonical operational endpoint is GET /api/v1/internal/detection-rules.
    """
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
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
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
def get_networks(
    limit: int = Query(default=50, ge=1, le=100, description="Max networks to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    networks_dict = compute_network_intelligence()
    all_networks = list(networks_dict.values())
    return all_networks[offset : offset + limit]



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

    try:
        from app.api.risk import compute_risk_summary
        risk_summary = compute_risk_summary()
        high_risk_accounts = int(risk_summary.get("high_risk_accounts", 0))
    except Exception:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(DISTINCT account_id)
                    FROM alerts
                    WHERE risk_score >= 60 OR risk_probability >= 0.60
                    """
                )
                row = cur.fetchone()
                high_risk_accounts = row[0] if row else 0

    return {
        "total_accounts": total_accounts,
        "suspicious_accounts": suspicious_accounts,
        "high_risk_accounts": high_risk_accounts,
        "total_transactions": total_transactions,
        "open_alerts": open_alerts,
        "active_cases": active_cases,
    }