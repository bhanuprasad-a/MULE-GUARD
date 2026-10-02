import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from collections import defaultdict, deque
from psycopg.rows import dict_row
from app.db.database import get_connection

def format_inr(val):
    val = float(val or 0)
    if val >= 10_000_000:
        return f"₹{val / 10_000_000:.2f} Cr"
    elif val >= 100_000:
        return f"₹{val / 100_000:.2f} Lakh"
    else:
        return f"₹{val:,.2f}".rstrip('0').rstrip('.')

def test_full_engine():
    conn = get_connection()
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT 
                a.id AS account_id,
                a.customer_id,
                a.account_type,
                a.balance,
                a.status,
                a.opened_at,
                c.name AS customer_name,
                c.phone,
                c.device_fingerprint,
                c.ip_address,
                c.address
            FROM accounts a
            LEFT JOIN customers c ON a.customer_id = c.id
        """)
        accounts_list = cur.fetchall()
        
        cur.execute("""
            SELECT 
                id,
                sender_account_id,
                receiver_account_id,
                amount,
                transaction_type,
                status,
                transaction_timestamp,
                origin,
                destination,
                created_at
            FROM transactions
            ORDER BY transaction_timestamp DESC
        """)
        tx_rows = cur.fetchall()

        cur.execute("SELECT account_id, risk_score, severity, status FROM alerts WHERE status != 'Resolved'")
        alerts_list = cur.fetchall()

    conn.close()

    print(f"Loaded {len(accounts_list)} accounts and {len(tx_rows)} transactions.")
    
    # Check sample mule loop: ACC-982050 .. ACC-982053
    loop_ids = ['ACC-982050', 'ACC-982051', 'ACC-982052', 'ACC-982053']
    loop_txs = [t for t in tx_rows if t['sender_account_id'] in loop_ids and t['receiver_account_id'] in loop_ids]
    print(f"Transactions inside loop cluster: {len(loop_txs)}")
    for t in loop_txs[:6]:
        print(f"  {t['sender_account_id']} -> {t['receiver_account_id']}: ₹{t['amount']}")

if __name__ == '__main__':
    test_full_engine()
