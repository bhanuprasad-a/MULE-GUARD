from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.api.auth import require_role


router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["Transactions"],
    dependencies=[Depends(require_role(["bank_investigator", "bank_compliance", "internal_team"]))],
)


class TransactionIngestSchema(BaseModel):
    sender_account_id: str | None = Field(default=None, max_length=64, alias="senderId")
    receiver_account_id: str | None = Field(default=None, max_length=64, alias="receiverId")
    amount: float = Field(..., gt=0.0, alias="amountNumeric", description="Transaction amount in INR, must be strictly greater than 0")
    transaction_type: str = Field(default="Transfer", max_length=64, alias="type")
    origin: str | None = Field(default=None, max_length=128)
    destination: str | None = Field(default=None, max_length=128)
    summary: str | None = Field(default=None, max_length=256)

    class Config:
        populate_by_name = True


@router.post("/ingest")
def ingest_transaction(payload: TransactionIngestSchema):
    tx_id = f"TX-{uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)

    # Determine accounts to lock in deterministic order (sorted) to prevent concurrent deadlocks
    accounts_to_lock = []
    if payload.sender_account_id:
        accounts_to_lock.append(payload.sender_account_id)
    if payload.receiver_account_id and payload.receiver_account_id not in accounts_to_lock:
        accounts_to_lock.append(payload.receiver_account_id)
    accounts_to_lock.sort()

    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                locked_accounts = {}
                for acc_id in accounts_to_lock:
                    cur.execute(
                        "SELECT id, balance, status FROM accounts WHERE id = %s FOR UPDATE",
                        (acc_id,)
                    )
                    row = cur.fetchone()
                    if not row:
                        role_name = "Sender" if acc_id == payload.sender_account_id else "Receiver"
                        raise HTTPException(404, f"{role_name} account {acc_id} not found")
                    locked_accounts[acc_id] = {
                        "balance": float(row[1]),
                        "status": row[2]
                    }

                # Verify sender account status and sufficient balance
                if payload.sender_account_id:
                    sender_info = locked_accounts[payload.sender_account_id]
                    if sender_info["status"] in ["Frozen", "Closed"]:
                        raise HTTPException(400, f"Sender account {payload.sender_account_id} is {sender_info['status']}")
                    if sender_info["balance"] < payload.amount:
                        raise HTTPException(400, "Insufficient funds")

                # Verify receiver account status
                if payload.receiver_account_id:
                    receiver_info = locked_accounts[payload.receiver_account_id]
                    if receiver_info["status"] in ["Frozen", "Closed"]:
                        raise HTTPException(400, f"Receiver account {payload.receiver_account_id} is {receiver_info['status']}")

                # Update balances atomically inside the transaction
                if payload.sender_account_id:
                    cur.execute(
                        "UPDATE accounts SET balance = balance - %s WHERE id = %s",
                        (payload.amount, payload.sender_account_id),
                    )

                if payload.receiver_account_id:
                    cur.execute(
                        "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                        (payload.amount, payload.receiver_account_id),
                    )

                # Insert transaction
                cur.execute(
                    """
                    INSERT INTO transactions (
                        id,
                        sender_account_id,
                        receiver_account_id,
                        amount,
                        transaction_type,
                        status,
                        transaction_timestamp,
                        origin,
                        destination
                    )
                    VALUES (%s, %s, %s, %s, %s, 'Completed', %s, %s, %s)
                    RETURNING id, transaction_timestamp
                    """,
                    (
                        tx_id,
                        payload.sender_account_id,
                        payload.receiver_account_id,
                        payload.amount,
                        payload.transaction_type,
                        now,
                        payload.origin or "System",
                        payload.destination or "System",
                    ),
                )
                tx_row = cur.fetchone()

                # Record in audit log
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
                        "TRANSACTION_INGESTED",
                        "transaction",
                        tx_id,
                        payload.receiver_account_id or payload.sender_account_id,
                        Jsonb({
                            "amount": payload.amount,
                            "sender_account_id": payload.sender_account_id,
                            "receiver_account_id": payload.receiver_account_id,
                            "type": payload.transaction_type,
                        }),
                    ),
                )

    return {
        "success": True,
        "transaction_id": tx_row[0],
        "sender_account_id": payload.sender_account_id,
        "receiver_account_id": payload.receiver_account_id,
        "amount": payload.amount,
        "status": "Completed",
        "timestamp": tx_row[1],
    }


@router.get("")
def get_transactions(
    limit: int = Query(default=100, ge=1, le=500, description="Max transactions to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.id,
                    t.sender_account_id,
                    t.receiver_account_id,
                    t.amount,
                    t.transaction_type,
                    t.status,
                    t.transaction_timestamp,
                    t.origin,
                    t.destination,
                    cs.name AS sender_name,
                    cr.name AS receiver_name
                FROM transactions t
                LEFT JOIN accounts sa ON t.sender_account_id = sa.id
                LEFT JOIN customers cs ON sa.customer_id = cs.id
                LEFT JOIN accounts ra ON t.receiver_account_id = ra.id
                LEFT JOIN customers cr ON ra.customer_id = cr.id
                ORDER BY t.transaction_timestamp DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "sender_account_id": r[1],
            "receiver_account_id": r[2],
            "senderId": r[1],
            "receiverId": r[2],
            "amount": float(r[3]),
            "amountNumeric": float(r[3]),
            "transaction_type": r[4],
            "type": r[4],
            "status": r[5],
            "transaction_timestamp": r[6].isoformat() if hasattr(r[6], "isoformat") else str(r[6]),
            "timestamp": r[6].isoformat() if hasattr(r[6], "isoformat") else str(r[6]),
            "origin": r[7] or "Mumbai",
            "destination": r[8] or "Delhi",
            "sender_name": r[9] or r[1],
            "receiver_name": r[10] or r[2],
            "entity": r[9] or r[1],
            "value": f"₹{int(r[3]):,}",
            "time": r[6].strftime("%Y-%m-%d %H:%M") if hasattr(r[6], "strftime") else str(r[6]),
        }
        for r in rows
    ]
