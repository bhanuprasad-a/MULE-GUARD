from app.db.database import get_connection

rules = [
    ('R-VEL-1', 'Velocity Spike (Inbound Degree)', 'Triggers when an account receives more than 5 inbound UPI transfers in a 24-hour period.', True),
    ('R-HOLD-1', 'Short Holding Time Ratio', 'Triggers when more than 80% of received funds are transferred out of the account within 30 minutes.', True),
    ('R-NET-1', 'Suspicious Component Connection', 'Triggers when a node has direct connection (shared device/IP/phone) to previously blocked/flagged fraud nodes.', True),
    ('R-VAL-1', 'High-Value Shell Transfer', 'Triggers on a transfer exceeding ₹1,00,000 from/to newly registered corporate shell entities.', True),
    ('R-CIRC-1', 'Circular Money Flow', 'Triggers when an account participates in a closed money flow loop of connected accounts.', True),
    ('R-DORM-1', 'Dormant Account Activation', 'Triggers when a previously inactive/dormant account receives significant transaction volume within 24 hours.', True),
]

with get_connection() as conn:
    with conn.cursor() as cur:
        for r in rules:
            cur.execute("""
                INSERT INTO rules (id, name, description, enabled)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    enabled = EXCLUDED.enabled
            """, r)
        conn.commit()
        cur.execute("SELECT count(*) FROM rules")
        print('Rules in DB now:', cur.fetchone()[0])
