from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.services.risk_engine import analyze_account
from app.api.auth import require_role


router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Alerts"],
    dependencies=[Depends(require_role(["bank_investigator", "bank_compliance"]))],
)


def get_severity(risk_score: float) -> str:
    if risk_score >= 80:
        return "Critical"
    if risk_score >= 60:
        return "High"
    if risk_score >= 30:
        return "Medium"
    return "Low"


@router.post("/analyze/{account_id}")
def analyze_and_create_alert(account_id: str = Path(..., max_length=64, description="Target account ID")):
    try:
        result = analyze_account(account_id)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        print("ANALYSIS ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Risk analysis failed",
        )

    risk_score = result["risk_score"]
    severity = get_severity(risk_score)

    alert_id = f"ALT-{uuid4().hex[:12].upper()}"

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Create alert
            cur.execute(
                """
                INSERT INTO alerts (
                    id,
                    account_id,
                    risk_score,
                    risk_probability,
                    prediction,
                    severity,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'Open'
                )
                RETURNING id, created_at
                """,
                (
                    alert_id,
                    account_id,
                    risk_score,
                    result["risk_probability"],
                    result["prediction"],
                    severity,
                ),
            )

            alert = cur.fetchone()

            # Evaluate deterministic detection rules
            from app.services.rule_engine import evaluate_rules_for_account
            rule_eval = evaluate_rules_for_account(account_id, conn=conn)
            triggered_rules = rule_eval.get("triggers", [])

            # Create audit log
            cur.execute(
                """
                INSERT INTO audit_logs (
                    action,
                    entity_type,
                    entity_id,
                    account_id,
                    details
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    "ALERT_CREATED",
                    "alert",
                    alert_id,
                    account_id,
                    Jsonb(
                        {
                            "risk_score": risk_score,
                            "prediction": result["prediction"],
                            "severity": severity,
                            "triggered_rules": triggered_rules,
                        }
                    ),
                ),
            )

    return {
        "alert_id": alert[0],
        "account_id": account_id,
        "risk_score": float(risk_score),
        "risk_probability": result["risk_probability"],
        "prediction": result["prediction"],
        "severity": severity,
        "status": "Open",
        "created_at": alert[1],
    }


@router.get("")
def get_alerts(
    limit: int = Query(default=100, ge=1, le=500, description="Max alerts to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.account_id,
                    a.risk_score,
                    a.risk_probability,
                    a.prediction,
                    a.severity,
                    a.status,
                    a.created_at,
                    c.name AS customer_name,
                    acc.account_type,
                    acc.balance
                FROM alerts a
                LEFT JOIN accounts acc ON a.account_id = acc.id
                LEFT JOIN customers c ON acc.customer_id = c.id
                ORDER BY a.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "alert_id": row[0],
            "account_id": row[1],
            "risk_score": float(row[2]),
            "risk_probability": float(row[3]),
            "prediction": row[4],
            "severity": row[5],
            "status": row[6],
            "created_at": row[7],
            "target": row[8] or row[1],
            "customer_name": row[8] or row[1],
            "account_type": row[9] or "Savings",
            "balance": float(row[10]) if row[10] is not None else 0.0,
            "category": "Velocity Anomaly" if float(row[2]) >= 80 else ("Structuring" if float(row[2]) >= 60 else "Behavioral Shift"),
            "amount": f"₹{int(row[10] or 50000):,}",
        }
        for row in rows
    ]


@router.get("/{alert_id}")
def get_alert(alert_id: str = Path(..., max_length=64, description="Target alert ID")):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.account_id,
                    a.risk_score,
                    a.risk_probability,
                    a.prediction,
                    a.severity,
                    a.status,
                    a.created_at,
                    c.name AS customer_name,
                    acc.account_type,
                    acc.balance
                FROM alerts a
                LEFT JOIN accounts acc ON a.account_id = acc.id
                LEFT JOIN customers c ON acc.customer_id = c.id
                WHERE a.id = %s
                """,
                (alert_id,),
            )

            row = cur.fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return {
        "id": row[0],
        "alert_id": row[0],
        "account_id": row[1],
        "risk_score": float(row[2]),
        "risk_probability": float(row[3]),
        "prediction": row[4],
        "severity": row[5],
        "status": row[6],
        "created_at": row[7],
        "target": row[8] or row[1],
        "customer_name": row[8] or row[1],
        "account_type": row[9] or "Savings",
        "balance": float(row[10]) if row[10] is not None else 0.0,
        "category": "Velocity Anomaly" if float(row[2]) >= 80 else ("Structuring" if float(row[2]) >= 60 else "Behavioral Shift"),
        "amount": f"₹{int(row[10] or 50000):,}",
    }


@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str = Path(..., max_length=64, description="Target alert ID")):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE alerts
                SET status = 'Acknowledged'
                WHERE id = %s
                RETURNING id, account_id, status
                """,
                (alert_id,),
            )

            row = cur.fetchone()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail="Alert not found",
                )

            # Create audit log
            cur.execute(
                """
                INSERT INTO audit_logs (
                    action,
                    entity_type,
                    entity_id,
                    account_id,
                    details
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    "ALERT_ACKNOWLEDGED",
                    "alert",
                    row[0],
                    row[1],
                    Jsonb(
                        {
                            "status": "Acknowledged",
                        }
                    ),
                ),
            )

    return {
        "alert_id": row[0],
        "account_id": row[1],
        "status": row[2],
    }