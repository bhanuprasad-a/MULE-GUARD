from fastapi import APIRouter, Depends

from app.db.database import get_connection
from app.api.auth import require_role


router = APIRouter(
    prefix="/api/v1/audit-logs",
    tags=["Audit Logs"],
    dependencies=[Depends(require_role(["internal_team", "bank_compliance"]))],
)


@router.get("")
def get_audit_logs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    action,
                    entity_type,
                    entity_id,
                    account_id,
                    details,
                    created_at
                FROM audit_logs
                ORDER BY created_at DESC
                """
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "action": row[1],
            "entity_type": row[2],
            "entity_id": row[3],
            "account_id": row[4],
            "details": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]