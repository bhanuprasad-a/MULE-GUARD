import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import get_connection
from app.services.network_engine import compute_network_intelligence
from app.services.risk_engine import analyze_account

def test_all():
    print("=== TESTING POSTGRESQL RUNTIME DERIVATIONS ===")
    
    # 1. Accounts & Customers
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM customers;")
            cust_cnt = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM accounts;")
            acc_cnt = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM transactions;")
            tx_cnt = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM accounts WHERE status = 'Normal';")
            legit_cnt = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM accounts WHERE status != 'Normal';")
            mule_cnt = cur.fetchone()[0]
            
            print(f"PostgreSQL customer count: {cust_cnt}")
            print(f"PostgreSQL account count:  {acc_cnt}")
            print(f"PostgreSQL tx count:       {tx_cnt}")
            print(f"Legitimate account count:  {legit_cnt}")
            print(f"Suspicious/mule count:     {mule_cnt}")

    # 2. Network Intelligence
    print("\n--- Testing Network Intelligence on PostgreSQL ---")
    networks = compute_network_intelligence()
    print(f"Networks computed from PostgreSQL transactions: {len(networks)}")
    for nid, net in list(networks.items())[:4]:
        print(f"  Network {nid}: {net['name']} | score={net['score']} | members={net['members']} | value={net['totalValue']}")

    # 3. Risk Engine on New Data
    print("\n--- Testing Risk Engine Inference on PostgreSQL ---")
    # Test on a legitimate account and on a mule account
    sample_legit = "ACC-982001"
    sample_mule = "ACC-982054" # Collector Hub
    res_legit = analyze_account(sample_legit)
    print(f"Legitimate account ({sample_legit}) -> Prediction: {res_legit['prediction']}, Prob: {res_legit['risk_probability']:.4f}, Score: {res_legit['risk_score']}")
    res_mule = analyze_account(sample_mule)
    print(f"Mule account ({sample_mule})       -> Prediction: {res_mule['prediction']}, Prob: {res_mule['risk_probability']:.4f}, Score: {res_mule['risk_score']}")

    print("\nALL POSTGRESQL RUNTIME SERVICES OPERATING CLEANLY!")

if __name__ == "__main__":
    test_all()
