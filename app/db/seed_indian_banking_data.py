"""
MuleGuard Indian Retail Banking Population Generator & PostgreSQL Importer
Seeds PostgreSQL as the authoritative single source of truth.
"""

import sys
import os
import random
import math
from datetime import datetime, timedelta, timezone

# Ensure project root is in sys.path
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_DIR)

from app.db.database import get_connection

# Set seed for deterministic reproducibility
random.seed(42)

# --- Configuration & Demographics ---
INDIAN_CITIES = [
    ("Vijayawada", "Andhra Pradesh", "5200"),
    ("Hyderabad", "Telangana", "5000"),
    ("Chennai", "Tamil Nadu", "6000"),
    ("Bengaluru", "Karnataka", "5600"),
    ("Mumbai", "Maharashtra", "4000"),
    ("Delhi", "Delhi", "1100"),
    ("Pune", "Maharashtra", "4110"),
    ("Kolkata", "West Bengal", "7000"),
    ("Visakhapatnam", "Andhra Pradesh", "5300"),
    ("Ahmedabad", "Gujarat", "3800"),
    ("Jaipur", "Rajasthan", "3020"),
    ("Kochi", "Kerala", "6820"),
    ("Lucknow", "Uttar Pradesh", "2260"),
    ("Guntur", "Andhra Pradesh", "5220"),
    ("Surat", "Gujarat", "3950"),
    ("Tirupati", "Andhra Pradesh", "5175"),
]

FIRST_NAMES_MALE = [
    "Rajesh", "Ramesh", "Suresh", "Vikram", "Venkata", "Arun", "Manoj", "Karthik",
    "Sanjay", "Deepak", "Ravi", "Aditya", "Amit", "Kishore", "Harish", "Murali",
    "Srinivas", "Sai", "Vijay", "Anand", "Naveen", "Pradeep", "Raghav", "Satish",
    "Gopal", "Dinesh", "Santosh", "Ashok", "Ganesh", "Mahesh", "Prakash", "Subhash"
]

FIRST_NAMES_FEMALE = [
    "Priya", "Sunita", "Ananya", "Kavita", "Lakshmi", "Divya", "Swati", "Sneha",
    "Pooja", "Meera", "Radhika", "Shreya", "Sandhya", "Gayathri", "Bhavani", "Preeti",
    "Usha", "Keerthi", "Aparna", "Deepa", "Vandana", "Sarita", "Rekha", "Padma",
    "Lavanya", "Geeta", "Shalini", "Madhavi", "Sowmya", "Rohini", "Sangeeta", "Anitha"
]

LAST_NAMES = [
    "Sharma", "Reddy", "Kumar", "Rao", "Patel", "Venkatesh", "Iyer", "Narayanan",
    "Joshi", "Verma", "Nair", "Kulkarni", "Gupta", "Deshmukh", "Choudhury", "Hegde",
    "Menon", "Bhat", "Pillai", "Varma", "Murthy", "Nambiar", "Sen", "Bose",
    "Mukherjee", "Raju", "Naidu", "Chowdary", "Sastry", "Chatterjee", "Aggarwal", "Mishra"
]

BUSINESS_NAMES = [
    ("Sri Venkateswara Kirana & General Stores", "Provisions & Groceries"),
    ("Annapurna Provisions & Rice Depot", "Wholesale Grains"),
    ("Sai Krupa Medical Agencies", "Retail Pharmacy"),
    ("Balaji Textiles & Handlooms", "Apparel & Fabrics"),
    ("Hyderabad Biryani Point & Caterers", "Food & Hospitality"),
    ("Modern Electronics & Mobile Spares", "Consumer Tech & Repairs"),
    ("Royal Auto Parts & Service", "Automotive Spares"),
    ("Krishna Milk & Dairy Parlour", "Dairy Products"),
    ("Padmavathi Agro Agencies", "Fertilizers & Farm Supplies"),
    ("Sri Rama Hardware & Electricals", "Building Materials"),
    ("Durga Stationery & Xerox Center", "Office Supplies"),
    ("Mahalaxmi Sweets & Bakery", "Confectionery"),
    ("Tirumala Tiffin Center & Hotel", "Restaurant"),
    ("Sree Valli Supermarket", "Retail Supermarket"),
    ("Surya Logistics & Packers", "Transport & Courier"),
    ("Sri Balaji Steel & Cement Traders", "Construction Supplies"),
    ("Vinayaka Tea Stall & Refreshments", "Beverages & Snacks"),
    ("Apex Opticals & Eye Clinic", "Healthcare & Eyewear"),
    ("Laxmi Footwear & Bags", "Footwear Retail"),
    ("Classic Men's Wear & Tailors", "Clothing & Tailoring"),
    ("New Metro Jewellers", "Jewellery & Ornaments"),
    ("Maruti Gas & Appliance Service", "Home Appliances"),
    ("Swathi Beauty Care & Cosmetics", "Cosmetics & Salon"),
    ("Kaveri Cold Drinks & Juice Bar", "Beverages"),
    ("Green Valley Nursery & Flowers", "Plants & Gardening"),
]

DEVICES = [
    "SAMSUNG_M34_5G", "REDMI_NOTE_13", "ONEPLUS_NORD_CE3", "VIVO_V29E", "REALME_12_PRO",
    "MOTO_G84_5G", "IPHONE_14", "IPHONE_13", "OPPO_RENO_11", "SAMSUNG_A54",
    "HP_PAVILION_15", "LENOVO_THINKPAD_E14", "DELL_INSPIRON_3520", "ACER_ASPIRE_5", "MACBOOK_AIR_M2"
]

# Realistic Indian Consumer IP Pools (Airtel, Jio, ACT, BSNL)
IP_PREFIXES = [
    "49.36.", "49.37.", "122.161.", "122.162.", "106.51.", "106.52.", "117.200.", "117.201.",
    "157.48.", "157.49.", "182.72.", "182.73."
]

USED_PHONES = set()

def generate_indian_ip():
    prefix = random.choice(IP_PREFIXES)
    return f"{prefix}{random.randint(1, 254)}.{random.randint(1, 254)}"

def generate_indian_phone():
    while True:
        first_digit = random.choice(["6", "7", "8", "9"])
        rest = "".join([str(random.randint(0, 9)) for _ in range(9)])
        phone = f"+91 {first_digit}{rest[:4]} {rest[4:]}"
        if phone not in USED_PHONES:
            USED_PHONES.add(phone)
            return phone

def generate_dataset():
    """
    Generates target Indian retail population:
    - 350 total accounts
    - 325 Individual customers (92.9%)
    - 25 Small Businesses (7.1%)
    - 295 Savings accounts (84.3%)
    - 55 Current accounts (15.7%)
    - 326 Legitimate accounts (93.1%)
    - 24 Mule / Suspicious accounts (6.9%)
    - Realistic retail transactions (predominantly ₹50 - ₹10,000)
    - Realistic graph and behavioral mule structures
    """
    now = datetime.now(timezone.utc)
    accounts = {}
    customers = {}
    transactions = []

    # 1. Generate Small Business Accounts (25 accounts)
    # ACC-982001 to ACC-982025
    business_account_ids = []
    for i, (biz_name, biz_category) in enumerate(BUSINESS_NAMES):
        acc_id = f"ACC-{982001 + i}"
        cust_id = f"CUST-{acc_id}"
        city, state, pin_prefix = random.choice(INDIAN_CITIES)
        city_pin = f"{pin_prefix}{random.randint(10, 99)}"
        phone = generate_indian_phone()
        device = random.choice(DEVICES)
        ip = generate_indian_ip()
        address = f"Shop No {random.randint(1, 45)}, Main Bazaar Road, {city}, {state} - {city_pin}"
        opened_at = now - timedelta(days=random.randint(180, 900))
        balance = round(random.uniform(45000, 380000), 2)

        customers[cust_id] = {
            "id": cust_id,
            "name": biz_name,
            "phone": phone,
            "device": device,
            "ip": ip,
            "address": address,
            "created_at": opened_at,
            "is_business": True,
            "category": biz_category
        }

        accounts[acc_id] = {
            "id": acc_id,
            "customer_id": cust_id,
            "name": biz_name,
            "account_type": "Current",
            "balance": balance,
            "initial_balance": balance,
            "status": "Normal",
            "risk_score": random.randint(12, 32),
            "opened_at": opened_at,
            "city": city,
            "is_mule": False,
            "mule_cluster": None
        }
        business_account_ids.append(acc_id)

    # 2. Design Mule & Suspicious Accounts (24 accounts, 6.9%)
    # Spread across ACC-982050 to ACC-982073
    mule_configs = []
    # Cluster 1: Rapid Movement & Circular Flow (Loop Ring) - 4 accounts
    for idx, (m_first, m_last) in enumerate([("Kalyan", "Chowdary"), ("Suresh", "Babu"), ("Venkatesh", "Naidu"), ("Ravi", "Teja")]):
        mule_configs.append({
            "name": f"{m_first} {m_last}",
            "type": "Savings",
            "cluster": "Circular Loop Ring",
            "status": "Under Review",
            "city": "Vijayawada",
            "risk_score": 82 + idx * 3
        })

    # Cluster 2: Fan-In / Aggregation (Collection Mule) - 6 accounts (1 hub, 1 exit, 4 conduits)
    for idx, (m_first, m_last, status, role) in enumerate([
        ("Sunil", "Verma", "Flagged", "Collector Hub"),
        ("Prashant", "Deshmukh", "Blocked", "Exit Node"),
        ("Anil", "Reddy", "Under Review", "Layer 1"),
        ("Manish", "Gupta", "Under Review", "Layer 2"),
        ("Vikram", "Pillai", "Under Review", "Layer 3"),
        ("Dinesh", "Karthik", "Under Review", "Layer 4")
    ]):
        mule_configs.append({
            "name": f"{m_first} {m_last}",
            "type": "Savings" if idx > 1 else "Current",
            "cluster": "Fan-In Collection Syndicate",
            "status": status,
            "city": "Hyderabad",
            "risk_score": 88 if "Hub" in role or "Exit" in role else 75
        })

    # Cluster 3: Fan-Out / Smurfing & Layering Dispersal - 6 accounts
    for idx, (m_first, m_last) in enumerate([
        ("Satish", "Raju"), ("Kishore", "Varma"), ("Naveen", "Goud"),
        ("Ganesh", "Iyer"), ("Mahesh", "Joshi"), ("Santosh", "Hegde")
    ]):
        mule_configs.append({
            "name": f"{m_first} {m_last}",
            "type": "Savings",
            "cluster": "Fan-Out Smurfing Ring",
            "status": "Flagged" if idx == 0 else "Under Review",
            "city": "Chennai",
            "risk_score": 85 if idx == 0 else 76
        })

    # Cluster 4: Dormant Account Sudden Activation - 4 accounts
    for idx, (m_first, m_last) in enumerate([
        ("Subhash", "Nair"), ("Prakash", "Chatterjee"), ("Harish", "Nambiar"), ("Gopal", "Sastry")
    ]):
        mule_configs.append({
            "name": f"{m_first} {m_last}",
            "type": "Savings",
            "cluster": "Dormant Activation Ring",
            "status": "Critical" if idx < 2 else "Under Review",
            "city": "Bengaluru",
            "risk_score": 91 if idx < 2 else 78
        })

    # Cluster 5: Shared Infrastructure Syndicate (Colocated Device/IP) - 4 accounts
    shared_device = "ONEPLUS_12_MULE_SHARED"
    shared_ip = "185.220.101.44"
    for idx, (m_first, m_last) in enumerate([
        ("Raghav", "Choudhury"), ("Ashok", "Kulkarni"), ("Dileep", "Mishra"), ("Sandesh", "Patel")
    ]):
        mule_configs.append({
            "name": f"{m_first} {m_last}",
            "type": "Savings",
            "cluster": "Shared Infrastructure Syndicate",
            "status": "Critical" if idx == 0 else "Flagged",
            "city": "Mumbai",
            "risk_score": 92 if idx == 0 else 84,
            "device": shared_device,
            "ip": shared_ip
        })

    mule_account_ids = []
    for i, m_conf in enumerate(mule_configs):
        acc_id = f"ACC-{982050 + i}"
        cust_id = f"CUST-{acc_id}"
        city = m_conf["city"]
        state = next((s for c, s, _ in INDIAN_CITIES if c == city), "Andhra Pradesh")
        pin = next((p for c, _, p in INDIAN_CITIES if c == city), "5000")
        city_pin = f"{pin}{random.randint(10, 99)}"
        phone = generate_indian_phone()
        device = m_conf.get("device", random.choice(DEVICES))
        ip = m_conf.get("ip", generate_indian_ip())
        address = f"Flat {random.randint(101, 804)}, Green Acres Colony, {city}, {state} - {city_pin}"
        
        # Dormant accounts opened 250+ days ago
        if "Dormant" in m_conf["cluster"]:
            opened_at = now - timedelta(days=random.randint(220, 360))
        else:
            opened_at = now - timedelta(days=random.randint(30, 180))

        balance = round(random.uniform(5000, 48000), 2)

        customers[cust_id] = {
            "id": cust_id,
            "name": m_conf["name"],
            "phone": phone,
            "device": device,
            "ip": ip,
            "address": address,
            "created_at": opened_at,
            "is_business": False
        }

        accounts[acc_id] = {
            "id": acc_id,
            "customer_id": cust_id,
            "name": m_conf["name"],
            "account_type": m_conf["type"],
            "balance": balance,
            "initial_balance": balance,
            "status": m_conf["status"],
            "risk_score": m_conf["risk_score"],
            "opened_at": opened_at,
            "city": city,
            "is_mule": True,
            "mule_cluster": m_conf["cluster"]
        }
        mule_account_ids.append(acc_id)

    # 3. Generate Legitimate Individual Customers (301 accounts)
    # Total accounts will be 25 (business) + 24 (mules) + 301 (legit individuals) = 350 accounts!
    # Legitimate count: 25 + 301 = 326 (93.14%)
    # Mule count: 24 (6.86%)
    # Savings count: 295 (84.29%)
    # Current count: 55 (15.71%) -> 25 businesses + 30 individual current accounts
    legit_individual_ids = []
    
    # 30 Individual Current Accounts (Professionals / Freelancers / Consultants)
    # Remaining 271 Individual Savings Accounts
    curr_counter = 982100
    for idx in range(301):
        acc_id = f"ACC-{curr_counter + idx}"
        cust_id = f"CUST-{acc_id}"
        
        is_male = random.random() > 0.5
        first = random.choice(FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        
        # First 30 are Current accounts, rest are Savings
        acct_type = "Current" if idx < 30 else "Savings"
        
        city, state, pin_prefix = random.choice(INDIAN_CITIES)
        city_pin = f"{pin_prefix}{random.randint(10, 99)}"
        phone = generate_indian_phone()
        device = random.choice(DEVICES)
        ip = generate_indian_ip()
        address = f"House No {random.randint(12, 140)}, Ward {random.randint(1, 18)}, {city}, {state} - {city_pin}"
        opened_at = now - timedelta(days=random.randint(45, 950))
        balance = round(random.uniform(12000, 240000), 2)

        customers[cust_id] = {
            "id": cust_id,
            "name": name,
            "phone": phone,
            "device": device,
            "ip": ip,
            "address": address,
            "created_at": opened_at,
            "is_business": False
        }

        accounts[acc_id] = {
            "id": acc_id,
            "customer_id": cust_id,
            "name": name,
            "account_type": acct_type,
            "balance": balance,
            "initial_balance": balance,
            "status": "Normal",
            "risk_score": random.randint(10, 34),
            "opened_at": opened_at,
            "city": city,
            "is_mule": False,
            "mule_cluster": None
        }
        legit_individual_ids.append(acc_id)

    all_legit_ids = business_account_ids + legit_individual_ids

    # 4. Generate Transactions
    # Retail Small denominations:
    RETAIL_SMALL_AMOUNTS = [50, 100, 150, 200, 250, 300, 450, 500, 750, 1000, 1200, 1500, 2000, 2500, 3000, 4500, 5000, 7500, 10000]
    tx_counter = 1

    def make_tx(sender_id, receiver_id, amount, tx_type, tx_time, origin, destination, summary):
        nonlocal tx_counter
        tx_id = f"TX-IND-{tx_counter:05d}"
        tx_counter += 1
        
        # Map to PostgreSQL check constraint: ('Transfer', 'Payment', 'Deposit', 'Withdrawal')
        valid_type_map = {
            "UPI": "Payment" if random.random() > 0.5 else "Transfer",
            "IMPS": "Transfer",
            "NEFT": "Deposit" if "salary" in (summary or "").lower() else "Transfer",
            "Payment": "Payment",
            "Transfer": "Transfer",
            "Deposit": "Deposit",
            "Withdrawal": "Withdrawal"
        }
        db_type = valid_type_map.get(tx_type, "Transfer")

        # Update running balances safely
        if sender_id and sender_id in accounts:
            accounts[sender_id]["balance"] -= amount
        if receiver_id and receiver_id in accounts:
            accounts[receiver_id]["balance"] += amount

        return {
            "id": tx_id,
            "sender_account_id": sender_id,
            "receiver_account_id": receiver_id,
            "amount": round(amount, 2),
            "transaction_type": db_type,
            "status": "Completed",
            "transaction_timestamp": tx_time,
            "origin": origin,
            "destination": destination,
            "summary": summary
        }

    # 4A. Normal Retail Transactions between legitimate accounts (2,400+ transactions)
    # Retail consumer payments: individuals paying businesses (Kirana, Pharmacy, Dining, etc.)
    # and peer-to-peer transfers (friends, family, rent, utilities)
    for _ in range(2500):
        sender = random.choice(legit_individual_ids)
        # 60% chance to pay a small business, 40% peer to peer
        if random.random() < 0.60:
            receiver = random.choice(business_account_ids)
            amount = float(random.choice(RETAIL_SMALL_AMOUNTS))
            tx_type = "Payment"
            summary = f"Retail UPI purchase at {accounts[receiver]['name']}"
        else:
            receiver = random.choice(legit_individual_ids)
            if sender == receiver:
                continue
            amount = float(random.choice(RETAIL_SMALL_AMOUNTS))
            tx_type = "Transfer"
            summary = "P2P funds transfer"

        # Check sender balance
        if accounts[sender]["balance"] < amount + 2000:
            continue

        days_ago = random.uniform(0.1, 28.0)
        tx_time = now - timedelta(days=days_ago, minutes=random.randint(0, 1440))
        tx = make_tx(
            sender, receiver, amount, tx_type, tx_time,
            accounts[sender]["city"], accounts[receiver]["city"], summary
        )
        transactions.append(tx)

    # 4B. Legitimate Larger Transactions: Salaries & Business Vendor Payments (250+ transactions)
    for b_id in business_account_ids:
        # Business pays suppliers / vendor payouts
        for _ in range(random.randint(3, 7)):
            supplier_id = random.choice([x for x in business_account_ids if x != b_id])
            amount = float(random.choice([25000, 35000, 48000, 65000, 82000, 110000]))
            if accounts[b_id]["balance"] < amount + 10000:
                continue
            days_ago = random.uniform(1.0, 25.0)
            tx_time = now - timedelta(days=days_ago)
            tx = make_tx(
                b_id, supplier_id, amount, "NEFT", tx_time,
                accounts[b_id]["city"], accounts[supplier_id]["city"],
                f"Commercial supplier settlement from {accounts[b_id]['name']}"
            )
            transactions.append(tx)

    # Regular salary deposits to individuals from businesses
    for ind_id in legit_individual_ids[:180]:
        payer = random.choice(business_account_ids)
        salary = float(random.choice([32000, 45000, 58000, 72000, 88000]))
        if accounts[payer]["balance"] < salary + 10000:
            continue
        days_ago = random.choice([5.0, 12.0, 20.0, 27.0])
        tx_time = now - timedelta(days=days_ago)
        tx = make_tx(
            payer, ind_id, salary, "NEFT", tx_time,
            accounts[payer]["city"], accounts[ind_id]["city"], "Monthly salary credit"
        )
        transactions.append(tx)

    # 4C. Mule Cluster 1: Circular Loop Flow (ACC-982050 -> ACC-982051 -> ACC-982052 -> ACC-982053 -> ACC-982050)
    # Rapid movement within minutes, cycleParticipation = 1
    mule_loop = mule_account_ids[0:4]
    loop_base_time = now - timedelta(hours=6)
    for cycle in range(3):
        loop_time = loop_base_time + timedelta(hours=cycle * 1.5)
        amount = 14500 + cycle * 1200
        for step in range(len(mule_loop)):
            s_acc = mule_loop[step]
            r_acc = mule_loop[(step + 1) % len(mule_loop)]
            step_time = loop_time + timedelta(minutes=step * 12)
            tx = make_tx(
                s_acc, r_acc, amount, "Transfer", step_time,
                accounts[s_acc]["city"], accounts[r_acc]["city"],
                f"Multi-hop circular flow segment {step + 1}"
            )
            transactions.append(tx)

    # 4D. Mule Cluster 2: Fan-In Aggregation Syndicate
    # Hub: mule_account_ids[4], Exit: mule_account_ids[5], Conduits: mule_account_ids[6:10]
    hub_acc = mule_account_ids[4]
    exit_acc = mule_account_ids[5]
    conduits = mule_account_ids[6:10]

    # Conduits receive multiple small deposits from external retail accounts
    fanin_time = now - timedelta(hours=14)
    for c_acc in conduits:
        for _ in range(4):
            f_sender = random.choice(legit_individual_ids)
            f_amount = float(random.choice([1500, 2500, 4000, 5000]))
            fanin_time += timedelta(minutes=15)
            tx = make_tx(
                f_sender, c_acc, f_amount, "UPI", fanin_time,
                accounts[f_sender]["city"], accounts[c_acc]["city"],
                "Layering collection conduit transfer"
            )
            transactions.append(tx)

        # Conduits funnel rapidly to Hub within 20 mins
        conduit_bal = 12000
        fanin_time += timedelta(minutes=10)
        tx = make_tx(
            c_acc, hub_acc, conduit_bal, "Transfer", fanin_time,
            accounts[c_acc]["city"], accounts[hub_acc]["city"],
            "Consolidated aggregation to clearing hub"
        )
        transactions.append(tx)

    # Hub sweeps out 92% of aggregated amount to Exit node in rapid movement
    fanin_time += timedelta(minutes=18)
    tx = make_tx(
        hub_acc, exit_acc, 44000, "IMPS", fanin_time,
        accounts[hub_acc]["city"], accounts[exit_acc]["city"],
        "Bulk outbound sweep to offshore gateway"
    )
    transactions.append(tx)

    # 4E. Mule Cluster 3: Fan-Out Smurfing Dispersal
    # Source mule_account_ids[10] disperses to mule_account_ids[11:16]
    source_mule = mule_account_ids[10]
    smurfs = mule_account_ids[11:16]
    smurf_time = now - timedelta(hours=22)
    # Source receives inbound
    f_source = random.choice(business_account_ids)
    tx = make_tx(
        f_source, source_mule, 38000, "Transfer", smurf_time,
        accounts[f_source]["city"], accounts[source_mule]["city"],
        "Corporate dispersal seeding"
    )
    transactions.append(tx)

    # Disperses into smaller sub-₹10k tranches rapidly
    for s_target in smurfs:
        smurf_time += timedelta(minutes=8)
        tx = make_tx(
            source_mule, s_target, 6500, "UPI", smurf_time,
            accounts[source_mule]["city"], accounts[s_target]["city"],
            "Smurfed rapid micro-dispersal tranche"
        )
        transactions.append(tx)

    # 4F. Mule Cluster 4: Dormant Account Sudden Activation
    # Dormant accounts: mule_account_ids[16], mule_account_ids[17]
    dormant_1 = mule_account_ids[16]
    dormant_2 = mule_account_ids[17]
    aggregator_mule = mule_account_ids[18]

    dorm_time = now - timedelta(hours=18)
    for dorm in [dormant_1, dormant_2]:
        for _ in range(3):
            dorm_time += timedelta(minutes=25)
            s_acc = random.choice(legit_individual_ids)
            tx = make_tx(
                s_acc, dorm, 18000, "UPI", dorm_time,
                accounts[s_acc]["city"], accounts[dorm]["city"],
                "Sudden dormant inbound spike"
            )
            transactions.append(tx)
        # Forward to aggregator within 25 min
        dorm_time += timedelta(minutes=20)
        tx = make_tx(
            dorm, aggregator_mule, 50000, "IMPS", dorm_time,
            accounts[dorm]["city"], accounts[aggregator_mule]["city"],
            "Immediate dormant funds drain"
        )
        transactions.append(tx)

    # 4G. Mule Cluster 5: Shared Infrastructure Syndicate
    # Colocated mules: mule_account_ids[20:24]
    colocated = mule_account_ids[20:24]
    colo_time = now - timedelta(hours=36)
    for i in range(len(colocated)):
        c1 = colocated[i]
        c2 = colocated[(i + 1) % len(colocated)]
        colo_time += timedelta(hours=2)
        tx = make_tx(
            c1, c2, 12500, "Transfer", colo_time,
            accounts[c1]["city"], accounts[c2]["city"],
            "Internal syndicate rebalancing"
        )
        transactions.append(tx)

    # Normalize balances so none are negative
    for acc in accounts.values():
        if acc["balance"] < 1000:
            acc["balance"] = round(random.uniform(5000, 25000), 2)
        else:
            acc["balance"] = round(acc["balance"], 2)

    # Sort transactions chronologically
    transactions.sort(key=lambda t: t["transaction_timestamp"])

    return accounts, customers, transactions


def insert_into_postgres(accounts, customers, transactions):
    """
    Clears existing demo records and inserts the new Indian retail banking population.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            print("[PostgreSQL] 1. Safely clearing old banking/demo records...")
            # Dependent tables first
            cur.execute("DELETE FROM audit_logs;")
            cur.execute("DELETE FROM decisions;")
            cur.execute("DELETE FROM cases;")
            cur.execute("DELETE FROM alerts;")
            cur.execute("DELETE FROM watchlists;")
            cur.execute("DELETE FROM transactions;")
            cur.execute("DELETE FROM accounts;")
            cur.execute("DELETE FROM customers;")
            cur.execute("DELETE FROM networks;")
            print("[PostgreSQL] Old tables cleared successfully.")

            print(f"[PostgreSQL] 2. Inserting {len(customers)} Indian customers...")
            for cust in customers.values():
                cur.execute(
                    """
                    INSERT INTO customers (
                        id, name, phone, device_fingerprint, ip_address, address, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        cust["id"],
                        cust["name"],
                        cust["phone"],
                        cust["device"],
                        cust["ip"],
                        cust["address"],
                        cust["created_at"]
                    )
                )

            print(f"[PostgreSQL] 3. Inserting {len(accounts)} accounts...")
            for acc in accounts.values():
                cur.execute(
                    """
                    INSERT INTO accounts (
                        id, customer_id, account_type, balance, status, opened_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        acc["id"],
                        acc["customer_id"],
                        acc["account_type"],
                        acc["balance"],
                        acc["status"],
                        acc["opened_at"]
                    )
                )

            print(f"[PostgreSQL] 4. Inserting {len(transactions)} retail transactions...")
            for tx in transactions:
                cur.execute(
                    """
                    INSERT INTO transactions (
                        id, sender_account_id, receiver_account_id, amount,
                        transaction_type, status, transaction_timestamp, origin, destination
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        tx["id"],
                        tx["sender_account_id"],
                        tx["receiver_account_id"],
                        tx["amount"],
                        tx["transaction_type"],
                        tx["status"],
                        tx["transaction_timestamp"],
                        tx["origin"],
                        tx["destination"]
                    )
                )

            print("[PostgreSQL] 5. Seeding initial detection alerts & cases for mule patterns...")
            # Generate alerts for flagged/critical accounts
            for acc in accounts.values():
                if acc["status"] in ("Flagged", "Critical", "Under Review"):
                    alert_id = f"ALT-{acc['id'].replace('ACC-', '')}"
                    sev = "Critical" if acc["risk_score"] >= 88 else ("High" if acc["risk_score"] >= 75 else "Medium")
                    cur.execute(
                        """
                        INSERT INTO alerts (
                            id, account_id, risk_score, risk_probability, prediction, severity, status, created_at
                        )
                        VALUES (%s, %s, %s, %s, 1, %s, 'Open', %s);
                        """,
                        (
                            alert_id,
                            acc["id"],
                            acc["risk_score"],
                            round(acc["risk_score"] / 100.0, 4),
                            sev,
                            acc["opened_at"] + timedelta(days=2)
                        )
                    )

                    # Create corresponding case for top priority alerts
                    if acc["status"] in ("Critical", "Flagged"):
                        case_id = f"CS-{acc['id'].replace('ACC-', '')}"
                        cur.execute(
                            """
                            INSERT INTO cases (
                                id, account_id, alert_id, title, status, priority, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, 'Open', %s, %s, %s);
                            """,
                            (
                                case_id,
                                acc["id"],
                                alert_id,
                                f"Suspicious Activity Review: {acc['name']} ({acc['mule_cluster'] or 'Risk Alert'})",
                                "High" if sev == "Critical" else "Medium",
                                acc["opened_at"] + timedelta(days=3),
                                acc["opened_at"] + timedelta(days=3)
                            )
                        )

            # Insert initial audit log
            cur.execute(
                """
                INSERT INTO audit_logs (
                    action, entity_type, entity_id, account_id, details, created_at
                )
                VALUES (%s, %s, %s, %s, %s, now());
                """,
                (
                    "DATABASE_INITIALIZED",
                    "system",
                    "SYSTEM",
                    None,
                    '{"details": "Indian retail banking population inserted as authoritative single source of truth"}'
                )
            )

        conn.commit()

    print("[PostgreSQL] Database commit successful!")


def main():
    print("=" * 68)
    print("  Generating New Fictional Indian Retail Banking Population")
    print("=" * 68)
    accounts, customers, transactions = generate_dataset()

    total_acc = len(accounts)
    total_cust = len(customers)
    total_tx = len(transactions)
    legit_cnt = sum(1 for a in accounts.values() if not a["is_mule"])
    mule_cnt = sum(1 for a in accounts.values() if a["is_mule"])
    biz_cnt = sum(1 for c in customers.values() if c.get("is_business"))
    savings_cnt = sum(1 for a in accounts.values() if a["account_type"] == "Savings")
    current_cnt = sum(1 for a in accounts.values() if a["account_type"] == "Current")

    print(f"Total Customers:    {total_cust} ({total_cust - biz_cnt} individuals [{(total_cust-biz_cnt)/total_cust*100:.1f}%], {biz_cnt} businesses [{biz_cnt/total_cust*100:.1f}%])")
    print(f"Total Accounts:     {total_acc} (Savings: {savings_cnt} [{savings_cnt/total_acc*100:.1f}%], Current: {current_cnt} [{current_cnt/total_acc*100:.1f}%])")
    print(f"Legitimate Accts:   {legit_cnt} ({legit_cnt/total_acc*100:.1f}%)")
    print(f"Mule/Suspicious:    {mule_cnt} ({mule_cnt/total_acc*100:.1f}%)")
    print(f"Total Transactions: {total_tx}")

    insert_into_postgres(accounts, customers, transactions)


if __name__ == "__main__":
    main()
