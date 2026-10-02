from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
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
    sender_account_id: str | None = Field(default=None, alias="senderId")
    receiver_account_id: str | None = Field(default=None, alias="receiverId")
    amount: float = Field(..., alias="amountNumeric")
    transaction_type: str = Field(default="Transfer", alias="type")
    origin: str | None = None
    destination: str | None = None
    summary: str | None = None

    class Config:
        populate_by_name = True


@router.post("/ingest")
def ingest_transaction(payload: TransactionIngestSchema):
    tx_id = f"TX-{uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Validate accounts if present
            if payload.sender_account_id:
                cur.execute("SELECT balance FROM accounts WHERE id = %s", (payload.sender_account_id,))
                sender_row = cur.fetchone()
                if not sender_row:
                    raise HTTPException(404, f"Sender account {payload.sender_account_id} not found")
                if sender_row[0] < payload.amount:
                    raise HTTPException(400, "Insufficient funds")

            if payload.receiver_account_id:
                cur.execute("SELECT id FROM accounts WHERE id = %s", (payload.receiver_account_id,))
                if not cur.fetchone():
                    raise HTTPException(404, f"Receiver account {payload.receiver_account_id} not found")

            # Update balances atomically
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
            row = cur.fetchone()

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
        "transaction_id": row[0],
        "sender_account_id": payload.sender_account_id,
        "receiver_account_id": payload.receiver_account_id,
        "amount": payload.amount,
        "status": "Completed",
        "timestamp": row[1],
    }


@router.get("")
def get_transactions(limit: int = 100):
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
                LIMIT %s
                """,
                (limit,),
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
