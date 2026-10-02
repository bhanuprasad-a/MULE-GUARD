import json
from datetime import datetime, timedelta

from app.db.database import get_connection


DATASET_PATH = "data/synthetic_db.json"


def parse_transaction_time(time_text: str) -> datetime:
    """
    Convert generator's relative time such as:
    '167 hrs ago'
    into a real timestamp.
    """
    hours = int(time_text.split()[0])
    return datetime.now() - timedelta(hours=hours)


def import_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    accounts = data["accounts"]
    transactions = data["transactions"]

    with get_connection() as conn:
        with conn.cursor() as cur:

            # -------------------------------------------------
            # 1. Clear existing imported banking data
            # -------------------------------------------------
            cur.execute("DELETE FROM transactions;")
            cur.execute("DELETE FROM accounts;")
            cur.execute("DELETE FROM customers;")

            # -------------------------------------------------
            # 2. Customers + Accounts
            # -------------------------------------------------
            for account in accounts.values():

                customer_id = f"CUST-{account['id']}"

                cur.execute(
                    """
                    INSERT INTO customers (
                        id,
                        name,
                        phone,
                        device_fingerprint,
                        ip_address,
                        address,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        customer_id,
                        account["name"],
                        account["phone"],
                        account["device"],
                        account["ip"],
                        account["address"],
                        datetime.strptime(
                            account["created"], "%Y-%m-%d"
                        ),
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO accounts (
                        id,
                        customer_id,
                        account_type,
                        balance,
                        status,
                        opened_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        account["id"],
                        customer_id,
                        account["type"],
                        account["balance"],
                        account["status"],
                        datetime.strptime(
                            account["created"], "%Y-%m-%d"
                        ),
                    ),
                )

            # -------------------------------------------------
            # 3. Transactions
            # -------------------------------------------------
            imported_transactions = 0
            skipped_transactions = 0

            for tx in transactions:

                sender_id = tx.get("senderId")
                receiver_id = tx.get("receiverId")

                # Map generator status to DB status
                source_status = tx.get("status", "Normal")

                if source_status == "Normal":
                    db_status = "Completed"
                elif source_status in (
                    "Pending",
                    "Completed",
                    "Failed",
                    "Reversed",
                ):
                    db_status = source_status
                else:
                    db_status = "Completed"

                transaction_type = tx.get("type", "Transfer")

                # Ensure only schema-supported transaction types
                if transaction_type not in (
                    "Transfer",
                    "Payment",
                    "Deposit",
                    "Withdrawal",
                ):
                    transaction_type = "Transfer"

                # Validate referenced accounts
                if sender_id and sender_id not in accounts:
                    skipped_transactions += 1
                    continue

                if receiver_id and receiver_id not in accounts:
                    skipped_transactions += 1
                    continue

                timestamp = parse_transaction_time(tx["time"])

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
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        tx["id"],
                        sender_id,
                        receiver_id,
                        tx["amountNumeric"],
                        transaction_type,
                        db_status,
                        timestamp,
                        tx.get("origin"),
                        tx.get("destination"),
                    ),
                )

                imported_transactions += 1

        conn.commit()

    print("\n--- PostgreSQL Import Complete ---")
    print(f"Customers:             {len(accounts)}")
    print(f"Accounts:              {len(accounts)}")
    print(f"Transactions imported: {imported_transactions}")
    print(f"Transactions skipped:  {skipped_transactions}")


if __name__ == "__main__":
    import_dataset()