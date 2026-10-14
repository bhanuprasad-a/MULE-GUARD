from fastapi import APIRouter, HTTPException, Depends, Query, Path
from app.db.database import get_connection
from app.api.auth import require_role


router = APIRouter(
    prefix="/api/v1/accounts",
    tags=["Accounts"],
    dependencies=[Depends(require_role(["bank_investigator", "bank_compliance", "internal_team"]))],
)


@router.get("")
def get_accounts(
    limit: int = Query(default=100, ge=1, le=500, description="Max number of accounts to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.customer_id,
                    c.name,
                    a.account_type,
                    a.balance,
                    a.status,
                    a.opened_at
                FROM accounts a
                JOIN customers c
                    ON c.id = a.customer_id
                ORDER BY a.id
                LIMIT %s OFFSET %s;
                """,
                (limit, offset),
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "customer_id": row[1],
            "name": row[2],
            "account_type": row[3],
            "balance": float(row[4]),
            "status": row[5],
            "opened_at": row[6],
        }
        for row in rows
    ]


@router.get("/{account_id}")
def get_account(account_id: str = Path(..., max_length=64, description="Target account ID")):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.customer_id,
                    c.name,
                    c.phone,
                    c.device_fingerprint,
                    c.ip_address,
                    c.address,
                    a.account_type,
                    a.balance,
                    a.status,
                    a.opened_at
                FROM accounts a
                JOIN customers c
                    ON c.id = a.customer_id
                WHERE a.id = %s;
                """,
                (account_id,),
            )

            row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return {
        "id": row[0],
        "customer_id": row[1],
        "name": row[2],
        "phone": row[3],
        "device_fingerprint": row[4],
        "ip_address": str(row[5]) if row[5] else None,
        "address": row[6],
        "account_type": row[7],
        "balance": float(row[8]),
        "status": row[9],
        "opened_at": row[10],
    }


@router.get("/{account_id}/transactions")
def get_account_transactions(
    account_id: str = Path(..., max_length=64, description="Target account ID"),
    limit: int = Query(default=100, ge=1, le=500, description="Max number of transactions to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT id FROM accounts WHERE id = %s;",
                (account_id,),
            )

            if cur.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Account not found",
                )

            cur.execute(
                """
                SELECT
                    id,
                    sender_account_id,
                    receiver_account_id,
                    amount,
                    transaction_type,
                    status,
                    transaction_timestamp,
                    origin,
                    destination
                FROM transactions
                WHERE
                    sender_account_id = %s
                    OR receiver_account_id = %s
                ORDER BY transaction_timestamp DESC
                LIMIT %s OFFSET %s;
                """,
                (account_id, account_id, limit, offset),
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "sender_account_id": row[1],
            "receiver_account_id": row[2],
            "amount": float(row[3]),
            "transaction_type": row[4],
            "status": row[5],
            "transaction_timestamp": row[6],
            "origin": row[7],
            "destination": row[8],
        }
        for row in rows
    ]