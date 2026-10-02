import time
from app.db.database import get_connection
from app.services.risk_engine import analyze_account

t0 = time.time()
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.id, a.customer_id, c.name, a.account_type, a.balance, a.status
            FROM accounts a
            JOIN customers c ON c.id = a.customer_id
            ORDER BY a.id
        """)
        accounts = cur.fetchall()

print(f"Fetched {len(accounts)} accounts in {time.time()-t0:.3f}s")

# Let's test computing risk for all non-normal accounts
t1 = time.time()
risk_results = {}
for acc in accounts:
    acc_id, cust_id, name, acc_type, balance, status = acc
    if status != 'Normal':
        res = analyze_account(acc_id)
        score = res['risk_score']
        prob = res['risk_probability']
    else:
        score = 0.38
        prob = 0.0038
    risk_results[acc_id] = {
        'id': acc_id,
        'name': name,
        'account_type': acc_type,
        'balance': float(balance),
        'status': status,
        'risk_score': score,
        'risk_probability': prob
    }

print(f"Calculated risk in {time.time()-t1:.3f}s")
# Tiers: Critical (>=80%), High (60-79%), Moderate (40-59%), Low (0-39%)
critical = [a for a in risk_results.values() if a['risk_score'] >= 80]
high = [a for a in risk_results.values() if 60 <= a['risk_score'] < 80]
moderate = [a for a in risk_results.values() if 40 <= a['risk_score'] < 60]
low = [a for a in risk_results.values() if a['risk_score'] < 40]

print(f"Tiers: Critical={len(critical)}, High={len(high)}, Moderate={len(moderate)}, Low={len(low)}")
print(f"Total = {len(critical)+len(high)+len(moderate)+len(low)}")
