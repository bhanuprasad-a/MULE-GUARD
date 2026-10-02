from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.api.auth import require_role


router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Cases"],
    dependencies=[Depends(require_role(["bank_investigator", "bank_compliance"]))],
)


@router.post("/from-alert/{alert_id}")
def create_case_from_alert(alert_id: str):
    case_id = f"CASE-{uuid4().hex[:12].upper()}"

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    account_id,
                    risk_score,
                    severity
                FROM alerts
                WHERE id = %s
                """,
                (alert_id,),
            )

            alert = cur.fetchone()

            if not alert:
                raise HTTPException(
                    status_code=404,
                    detail="Alert not found",
                )

            alert_id_db = alert[0]
            account_id = alert[1]
            risk_score = float(alert[2])
            severity = alert[3]

            cur.execute(
                """
                SELECT id
                FROM cases
                WHERE alert_id = %s
                """,
                (alert_id,),
            )

            if cur.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="Case already exists for this alert",
                )

            cur.execute(
                """
                INSERT INTO cases (
                    id,
                    account_id,
                    alert_id,
                    title,
                    status,
                    priority
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'Open',
                    %s
                )
                RETURNING id, created_at, updated_at
                """,
                (
                    case_id,
                    account_id,
                    alert_id_db,
                    f"Mule risk investigation - {account_id}",
                    severity,
                ),
            )

            case = cur.fetchone()

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
                    "CASE_CREATED",
                    "case",
                    case_id,
                    account_id,
                    Jsonb({
                        "alert_id": alert_id,
                        "risk_score": risk_score,
                        "severity": severity,
                    }),
                ),
            )

    return {
        "case_id": case[0],
        "account_id": account_id,
        "alert_id": alert_id,
        "title": f"Mule risk investigation - {account_id}",
        "status": "Open",
        "priority": severity,
        "created_at": case[1],
        "updated_at": case[2],
    }


@router.get("")
def get_cases():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.id,
                    c.account_id,
                    c.alert_id,
                    c.title,
                    c.status,
                    c.priority,
                    c.created_at,
                    c.updated_at,
                    cust.name AS customer_name,
                    acc.account_type,
                    acc.balance
                FROM cases c
                LEFT JOIN accounts acc ON c.account_id = acc.id
                LEFT JOIN customers cust ON acc.customer_id = cust.id
                ORDER BY c.created_at DESC
                """
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "case_id": row[0],
            "account_id": row[1],
            "alert_id": row[2],
            "title": row[3],
            "status": row[4],
            "priority": row[5],
            "created_at": row[6],
            "updated_at": row[7],
            "entity": row[8] or row[1],
            "customer_name": row[8] or row[1],
            "account_type": row[9] or "Savings",
            "balance": float(row[10]) if row[10] is not None else 0.0,
            "amount": f"₹{int(row[10] or 100000):,}",
            "assignee": "A. Kumar",
            "createdTime": row[6].strftime("%Y-%m-%d %H:%M") if hasattr(row[6], "strftime") else str(row[6]),
        }
        for row in rows
    ]


@router.get("/{case_id}")
def get_case(case_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.id,
                    c.account_id,
                    c.alert_id,
                    c.title,
                    c.status,
                    c.priority,
                    c.created_at,
                    c.updated_at,
                    cust.name AS customer_name,
                    acc.account_type,
                    acc.balance
                FROM cases c
                LEFT JOIN accounts acc ON c.account_id = acc.id
                LEFT JOIN customers cust ON acc.customer_id = cust.id
                WHERE c.id = %s
                """,
                (case_id,),
            )

            row = cur.fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return {
        "id": row[0],
        "case_id": row[0],
        "account_id": row[1],
        "alert_id": row[2],
        "title": row[3],
        "status": row[4],
        "priority": row[5],
        "created_at": row[6],
        "updated_at": row[7],
        "entity": row[8] or row[1],
        "customer_name": row[8] or row[1],
        "account_type": row[9] or "Savings",
        "balance": float(row[10]) if row[10] is not None else 0.0,
        "amount": f"₹{int(row[10] or 100000):,}",
        "assignee": "A. Kumar",
        "createdTime": row[6].strftime("%Y-%m-%d %H:%M") if hasattr(row[6], "strftime") else str(row[6]),
    }


def change_status(case_id: str, new_status: str):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE cases
                SET
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, account_id, status, updated_at
                """,
                (new_status, case_id),
            )

            row = cur.fetchone()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail="Case not found",
                )

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
                    f"CASE_{new_status.upper()}",
                    "case",
                    row[0],
                    row[1],
                    Jsonb({
                        "status": new_status,
                    }),
                ),
            )

    return {
        "case_id": row[0],
        "account_id": row[1],
        "status": row[2],
        "updated_at": row[3],
    }


@router.patch("/{case_id}/investigate")
def investigate_case(case_id: str):
    return change_status(case_id, "Investigating")


@router.patch("/{case_id}/escalate")
def escalate_case(case_id: str):
    return change_status(case_id, "Escalated")


@router.patch("/{case_id}/resolve")
def resolve_case(case_id: str):
    return change_status(case_id, "Resolved")