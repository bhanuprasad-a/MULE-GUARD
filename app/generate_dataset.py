import os
import json
import random
import numpy as np

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)

# Helper lists for synthetic data generation
CITIES = ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad", "Surat", "Jaipur", "Lucknow", "Kochi", "Guwahati", "Bhopal"]
DEVICES = ["IPHONE_15_PRO", "IPHONE_14", "SAMSUNG_S24", "SAMSUNG_A54", "MACBOOK_PRO_M3", "MACBOOK_AIR", "THINKPAD_T14", "DELL_LATITUDE", "IPAD_AIR", "SAMSUNG_TAB_S9"]
IPS = [f"192.168.4.{i}" for i in range(10, 200)] + [f"10.15.22.{i}" for i in range(10, 200)] + [f"172.16.89.{i}" for i in range(10, 200)]

def generate_db():
    accounts = {}
    transactions = []
    
    # Track scenario label for each account for metric reporting
    scenario_labels = {}
    
    # We will generate ~250 accounts total
    acc_counter = 982000
    
    def next_acc_id():
        nonlocal acc_counter
        acc_counter += 1
        return f"ACC-{acc_counter}"
        
    def get_relative_time_str(offset_minutes):
        if offset_minutes < 60:
            return f"{offset_minutes} min ago"
        else:
            hrs = offset_minutes // 60
            return f"{hrs} hr{'s' if hrs > 1 else ''} ago"

    # --- Scenario 1: Normal Legitimate Users (130 accounts) ---
    normal_ids = []
    for _ in range(130):
        aid = next_acc_id()
        normal_ids.append(aid)
        scenario_labels[aid] = "Normal Legitimate"
        accounts[aid] = {
            "id": aid,
            "name": f"Legit User {random.randint(100, 999)}",
            "type": "Savings" if random.random() > 0.3 else "Current",
            "balance": round(random.uniform(15000, 180000), 2),
            "riskScore": random.randint(15, 35),
            "status": "Normal",
            "created": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "phone": f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Flat {random.randint(101, 909)}, Sector {random.randint(1, 25)}, {random.choice(CITIES)}"
        }

    # --- Scenario 2: Legitimate High-Volume Users (30 accounts) ---
    business_ids = []
    for _ in range(30):
        aid = next_acc_id()
        business_ids.append(aid)
        scenario_labels[aid] = "Legitimate High-Volume"
        accounts[aid] = {
            "id": aid,
            "name": f"LogiCorp {random.randint(100, 999)} Ltd",
            "type": "Current",
            "balance": round(random.uniform(200000, 2500000), 2), # Some lower balances overlapping with normal users
            "riskScore": random.randint(25, 45),
            "status": "Normal",
            "created": f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "phone": f"+91 90110 {random.randint(50000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Building {random.randint(10, 80)}, Business District, {random.choice(CITIES)}"
        }

    # --- Scenario 3: Mule Accounts (Rapid Receive-to-Send) (25 accounts) ---
    mule_rapid_ids = []
    for _ in range(25):
        aid = next_acc_id()
        mule_rapid_ids.append(aid)
        scenario_labels[aid] = "Mule Rapid Forwarding"
        accounts[aid] = {
            "id": aid,
            "name": f"Shell Partner {random.randint(100, 999)}",
            "type": "Current" if random.random() > 0.2 else "Savings", # Savings account mules exist (overlap)
            "balance": round(random.uniform(1000, 45000), 2), # Some higher balances
            "riskScore": random.randint(85, 98),
            "status": "Flagged" if random.random() > 0.4 else "Critical",
            "created": f"2026-01-{random.randint(1, 28):02d}",
            "phone": f"+91 {random.randint(60000, 69999)} {random.randint(10000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Room {random.randint(1, 12)}, Chawl No {random.randint(1, 15)}, {random.choice(CITIES)}"
        }

    # --- Scenario 4: Smurfing Sweeper & Smurfs (15 sweepers, 30 smurfs) ---
    smurf_sweeper_ids = []
    smurf_ids = []
    for _ in range(15):
        sweeper_id = next_acc_id()
        smurf_sweeper_ids.append(sweeper_id)
        scenario_labels[sweeper_id] = "Smurfing Sweeper"
        accounts[sweeper_id] = {
            "id": sweeper_id,
            "name": f"Smurf Receiver {random.randint(100, 999)}",
            "type": "Current" if random.random() > 0.3 else "Savings",
            "balance": round(random.uniform(2000, 60000), 2),
            "riskScore": random.randint(75, 95),
            "status": "Flagged",
            "created": f"2025-06-{random.randint(1, 28):02d}",
            "phone": f"+91 80000 {random.randint(10000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Commercial Plaza, {random.choice(CITIES)}"
        }
        # Add 2 smurf accounts per sweeper
        for _ in range(2):
            smurf_id = next_acc_id()
            smurf_ids.append(smurf_id)
            scenario_labels[smurf_id] = "Smurfing Contributor"
            accounts[smurf_id] = {
                "id": smurf_id,
                "name": f"Retail Account {random.randint(1000, 9999)}",
                "type": "Savings",
                "balance": round(random.uniform(3000, 15000), 2),
                "riskScore": random.randint(40, 60),
                "status": "Normal",
                "created": f"2024-11-{random.randint(1, 28):02d}",
                "phone": f"+91 70000 {random.randint(10000, 99999)}",
                "device": random.choice(DEVICES),
                "ip": random.choice(IPS),
                "address": f"Residential Society, {random.choice(CITIES)}"
            }

    # --- Scenario 5: Layering Chain accounts (20 accounts) ---
    layering_ids = []
    for _ in range(20):
        aid = next_acc_id()
        layering_ids.append(aid)
        scenario_labels[aid] = "Layering Conduit"
        accounts[aid] = {
            "id": aid,
            "name": f"Trading Conduit {random.randint(100, 999)}",
            "type": "Current",
            "balance": round(random.uniform(5000, 150000), 2),
            "riskScore": random.randint(65, 88),
            "status": "Under Review",
            "created": f"2025-02-{random.randint(1, 28):02d}",
            "phone": f"+91 99900 {random.randint(10000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Industrial Area Phase 2, {random.choice(CITIES)}"
        }

    # --- Scenario 6: Mule Rings sharing device/IP (10 accounts) ---
    ring_ids = []
    shared_device = "IPHONE_15_PRO"
    shared_ip = "192.168.4.15"
    for _ in range(10):
        aid = next_acc_id()
        ring_ids.append(aid)
        scenario_labels[aid] = "Mule Ring Member"
        accounts[aid] = {
            "id": aid,
            "name": f"Ring Node {random.randint(100, 999)}",
            "type": "Current",
            "balance": round(random.uniform(2000, 65000), 2),
            "riskScore": random.randint(80, 96),
            "status": "Flagged",
            "created": f"2025-08-{random.randint(1, 28):02d}",
            "phone": f"+91 90110 {random.randint(10000, 49999)}",
            "device": shared_device,
            "ip": shared_ip,
            "address": "12th Floor, Apex Towers, Mumbai"
        }

    # --- Scenario 7: Circular Loop Accounts (6 accounts) ---
    loop_ids = []
    for _ in range(6):
        aid = next_acc_id()
        loop_ids.append(aid)
        scenario_labels[aid] = "Circular Loop Node"
        accounts[aid] = {
            "id": aid,
            "name": f"Loop Transit {random.randint(100, 999)}",
            "type": "Current",
            "balance": round(random.uniform(5000, 75000), 2),
            "riskScore": random.randint(70, 88),
            "status": "Under Review",
            "created": f"2025-04-{random.randint(1, 28):02d}",
            "phone": f"+91 88877 {random.randint(10000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Market Road, {random.choice(CITIES)}"
        }

    # --- Scenario 8: Sudden Behavioural Shifts (10 accounts) ---
    shift_ids = []
    for _ in range(10):
        aid = next_acc_id()
        shift_ids.append(aid)
        scenario_labels[aid] = "Sudden Behavioural Shift"
        accounts[aid] = {
            "id": aid,
            "name": f"Dormant Account {random.randint(100, 999)}",
            "type": "Savings",
            "balance": round(random.uniform(50000, 500000), 2),
            "riskScore": random.randint(78, 97),
            "status": "Flagged",
            "created": "2023-01-15",
            "phone": f"+91 95550 {random.randint(10000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Residential Housing Board, {random.choice(CITIES)}"
        }

    # --- Scenario 9: Difficult Legitimate Edge Cases (15 accounts) ---
    edge_ids = []
    for _ in range(15):
        aid = next_acc_id()
        edge_ids.append(aid)
        scenario_labels[aid] = "Difficult Legitimate Edge Case"
        accounts[aid] = {
            "id": aid,
            "name": f"High Growth Freelancer {random.randint(100, 999)}",
            "type": "Current",
            "balance": round(random.uniform(200000, 1200000), 2),
            "riskScore": random.randint(45, 65),
            "status": "Normal",
            "created": f"2024-03-{random.randint(1, 28):02d}",
            "phone": f"+91 97770 {random.randint(10000, 99999)}",
            "device": random.choice(DEVICES),
            "ip": random.choice(IPS),
            "address": f"Co-working Space, {random.choice(CITIES)}"
        }

    # Write Scenario Labels to accounts for analysis metadata
    for aid, label in scenario_labels.items():
        accounts[aid]["scenario"] = label

    # --- Generate Transactions Ledger (~2500 transactions) ---
    tx_counter = 1
    def add_tx(sender, receiver, amount, status="Normal", delay_mins=10, summary="Standard transfer."):
        nonlocal tx_counter
        tid = f"TX-GEN-{tx_counter:04d}"
        tx_counter += 1
        transactions.append({
            "id": tid,
            "senderId": sender,
            "receiverId": receiver,
            "amountNumeric": amount,
            "type": "Transfer" if random.random() > 0.2 else "Payment",
            "value": f"₹{amount:,.0f}" if amount >= 1000 else f"₹{amount:,.2f}",
            "score": random.randint(10, 99),
            "time": get_relative_time_str(delay_mins),
            "origin": random.choice(CITIES),
            "destination": random.choice(CITIES),
            "status": status,
            "summary": summary
        })

    # 1. Normal users transactions (with noise, Legitimate loops, high-velocity outliers)
    # Generate 3-18 historical transactions per normal user, creating overlap with suspicious counts
    for uid in normal_ids:
        # A subset of normal users (15%) behaves with higher velocity (10-18 transactions)
        tx_count_limit = random.randint(10, 18) if random.random() < 0.15 else random.randint(3, 8)
        for _ in range(tx_count_limit):
            other = random.choice(normal_ids)
            if other != uid:
                # Highly overlapping amounts: up to 120,000 INR
                amt = round(random.uniform(200, 120000))
                time_offset = random.randint(10, 14400) # Spaced over up to 10 days
                add_tx(uid, other, amt, delay_mins=time_offset)

    # Legitimate Loops among normal users: select groups of 3 and create circular payments (A -> B -> C -> A)
    # This adds cycle participation to legitimate accounts
    for i in range(12):
        u1 = normal_ids[i * 3]
        u2 = normal_ids[i * 3 + 1]
        u3 = normal_ids[i * 3 + 2]
        amt = round(random.uniform(500, 15000))
        time_offset = random.randint(100, 5000)
        add_tx(u1, u2, amt, delay_mins=time_offset + 120, summary="Split dinner share.")
        add_tx(u2, u3, amt, delay_mins=time_offset + 60, summary="Settlement transfer.")
        add_tx(u3, u1, amt, delay_mins=time_offset + 5, summary="Repayment loan.")

    # 2. Legitimate High-Volume Business transactions (highly noisy)
    # Generate 6-25 transactions per business account
    for bid in business_ids:
        tx_count_limit = random.randint(6, 25)
        for _ in range(tx_count_limit):
            # Connect to random normal accounts (counterparty overlap)
            other = random.choice(normal_ids + business_ids)
            if other != bid:
                # Large values overlapping with money laundering layering sizes
                amt = round(random.uniform(10000, 350000))
                time_offset = random.randint(5, 10000)
                add_tx(bid, other, amt, delay_mins=time_offset, summary="Vendor payment dispatch.")

    # 3. Mule Accounts (Rapid Receive-to-Send with randomized holding times & loops)
    for mid in mule_rapid_ids:
        # Randomized iterations (1 to 5 loops)
        loops = random.randint(1, 5)
        for i in range(loops):
            # Overlapping amount sizes
            inbound_amt = round(random.uniform(15000, 160000))
            source = random.choice(normal_ids)
            target = random.choice(normal_ids)
            # Randomized delay - some hold funds for up to 12 hours (creating temporal proximity overlap)
            delay = random.randint(2, 720) 
            time_offset = random.randint(10, 8000)
            
            # Inbound deposit
            add_tx(source, mid, inbound_amt, delay_mins=time_offset + delay, summary=" UPI deposit credit.")
            # Outbound sweep (99% matched volume)
            add_tx(mid, target, inbound_amt - random.randint(10, 800), delay_mins=time_offset, summary="External account sweep.")

    # 4. Smurfing Sweeper & Smurfs (noisy deposits and counts)
    for sweeper in smurf_sweeper_ids:
        # Sweeper receives 2 to 8 micro-deposits
        inflows = random.randint(2, 8)
        total_smurfed = 0
        time_offset = random.randint(100, 8000)
        for idx in range(inflows):
            smurf = random.choice(smurf_ids + normal_ids) # Include normal users as noisy sources
            amt = round(random.uniform(1500, 15000)) # Micro-deposit overlapping with standard P2P
            total_smurfed += amt
            add_tx(smurf, sweeper, amt, delay_mins=time_offset + (idx * 45), summary="Immediate UPI transfer.")
            
        # Outflow sweep
        recipient = random.choice(layering_ids)
        add_tx(sweeper, recipient, total_smurfed - random.randint(50, 400), delay_mins=time_offset, summary="Consolidated fund route.")

    # 5. Layering chains with noisy hops and delays
    for idx in range(10):
        # Chain nodes
        a = random.choice(normal_ids)
        b = layering_ids[idx * 2]
        c = layering_ids[idx * 2 + 1]
        d = random.choice(normal_ids)
        
        amt = round(random.uniform(50000, 250000))
        # Large temporal spacing between hops (some immediate, some delayed by hours)
        delay_ab = random.randint(5, 180)
        delay_bc = random.randint(5, 360)
        delay_cd = random.randint(5, 720)
        time_offset = random.randint(100, 5000)
        
        add_tx(a, b, amt, delay_mins=time_offset + delay_ab + delay_bc + delay_cd)
        add_tx(b, c, amt - random.randint(200, 2000), delay_mins=time_offset + delay_bc + delay_cd)
        add_tx(c, d, amt - random.randint(400, 4000), delay_mins=time_offset + delay_cd)

    # 6. Mule Ring Members (randomized mutual transactions)
    for idx in range(len(ring_ids)):
        r_node = ring_ids[idx]
        next_node = ring_ids[(idx + 1) % len(ring_ids)]
        amt = round(random.uniform(10000, 110000))
        time_offset = random.randint(10, 6000)
        # Netting loop
        add_tx(r_node, next_node, amt, delay_mins=time_offset, summary="Corporate settlement.")
        # Introduce connection to innocent normal users (noisy degree)
        if random.random() > 0.4:
            add_tx(random.choice(normal_ids), r_node, amt + random.randint(1000, 5000), delay_mins=time_offset + 30)

    # 7. Circular loop Accounts (noisy circular transit)
    for idx in range(3):
        n1 = loop_ids[idx * 2]
        n2 = loop_ids[idx * 2 + 1]
        n3 = random.choice(loop_ids)
        if n3 in [n1, n2]:
            n3 = loop_ids[(idx * 2 + 2) % len(loop_ids)]
            
        amt = round(random.uniform(15000, 95000))
        time_offset = random.randint(50, 4000)
        
        add_tx(n1, n2, amt, delay_mins=time_offset + 60)
        add_tx(n2, n3, amt, delay_mins=time_offset + 30)
        add_tx(n3, n1, amt, delay_mins=time_offset + 5)

    # 8. Sudden Behavioural Shifts (dormant spikes with randomized velocity)
    for shift_id in shift_ids:
        # Spikes: random 2 to 7 transactions in the last 4 hours
        spikes = random.randint(2, 7)
        time_offset = random.randint(5, 240)
        for k in range(spikes):
            source = random.choice(normal_ids)
            amt = round(random.uniform(40000, 220000))
            add_tx(source, shift_id, amt, delay_mins=time_offset + k*10)

    # 9. Difficult Legitimate Edge Cases (highly active freelancers/shops)
    for eid in edge_ids:
        # High count of counterparties and balance changes resembling sweepers
        for k in range(random.randint(6, 12)):
            other = random.choice(normal_ids)
            amt = round(random.uniform(5000, 300000))
            time_offset = random.randint(100, 8000)
            add_tx(eid, other, amt, delay_mins=time_offset)
            if random.random() > 0.3:
                add_tx(other, eid, amt - random.randint(50, 1500), delay_mins=time_offset + random.randint(10, 180))

    # Generate Alerts and Cases
    alerts = []
    cases = []
    
    alert_counter = 982700
    case_counter = 982700
    
    for aid, acc in accounts.items():
        if acc["status"] != "Normal":
            alert_counter += 1
            case_counter += 1
            
            al_id = f"AL-{alert_counter}"
            cs_id = f"CS-{case_counter}"
            
            alerts.append({
                "id": al_id,
                "target": acc["name"],
                "category": "Behavioral Anomaly" if acc["status"] == "Under Review" else "Velocity Spike",
                "score": acc["riskScore"],
                "amount": f"₹{random.randint(50, 450)},000",
                "time": "12 min ago",
                "severity": "Critical" if acc["riskScore"] >= 90 else "High",
                "status": "New",
                "summary": f"Behavioral profiler triggered alert for {acc['name']}.",
                "indicators": [f"Risk score at {acc['riskScore']}"],
                "riskExplanation": f"Target entity matches structured indicators matching the `{acc.get('scenario', 'Mule')}` profile.",
                "notes": "Pending audit.",
                "caseId": cs_id
            })
            
            cases.append({
                "id": cs_id,
                "title": f"{acc['name']} AML Review",
                "entity": acc["name"],
                "primaryEntityId": aid,
                "priority": "Critical" if acc["riskScore"] >= 90 else "High",
                "score": acc["riskScore"],
                "assignee": random.choice(["S. Rao", "R. Singh", "A. Kumar"]),
                "createdTime": "2 hrs ago",
                "lastUpdated": "10 min ago",
                "status": "Investigating" if acc["status"] == "Under Review" else "Escalated",
                "summary": f"System engine detected {acc.get('scenario', 'Mule')} characteristics.",
                "findings": [
                    "High velocity spike matched to synthetic rule engines",
                    "Device connection fingerprint audit flag triggered"
                ],
                "notes": "Awaiting ledger reviews.",
                "activity": [
                    { "time": "10 min ago", "text": "Investigation logged" }
                ]
            })

    decisions = [
        {
            "id": "DEC-001",
            "caseId": "CS-982701",
            "caseTitle": "Mule Ring Member Review",
            "decision": "Reject / Block",
            "rationale": "Direct shared device matched to verified ring hubs.",
            "timestamp": "Just now",
            "reviewer": "A. Kumar"
        }
    ]

    audit_logs = [
        {
            "id": "LOG-001",
            "actor": "System Engine",
            "action": "Generated reproducible noisy synthetic dataset",
            "time": "Just now",
            "details": f"Loaded {len(accounts)} accounts and {len(transactions)} transactions."
        }
    ]

    networks = {
        'NET-082714': {
            "id": "NET-082714",
            "name": "Apex-Northstar Link",
            "type": "Shell Conduit",
            "score": 95,
            "members": 5,
            "totalValue": "₹96,90,000",
            "connectedCount": 12,
            "lastActivity": "8 min ago",
            "status": "Flagged",
            "summary": "Apex-Northstar loop link nodes.",
            "graphNodes": [
                { "id": "ACC-982741", "label": "Apex Hub", "role": "Treasury Node", "risk": "Critical", "cx": 200, "cy": 80, "r": 16 },
                { "id": "ACC-982714", "label": "Northstar", "role": "Receiver", "risk": "Critical", "cx": 80, "cy": 40, "r": 12 }
            ],
            "graphLinks": [
                { "source": 0, "target": 1, "flow": True }
            ]
        }
    }

    db_out = {
        "rules": [
            { "id": "R-VEL-1", "name": "Velocity Spike (Inbound Degree)", "threshold": 5, "unit": "transfers/24h", "description": "Triggers when an account receives more than the threshold of inbound UPI transfers in a 24-hour period.", "active": True },
            { "id": "R-HOLD-1", "name": "Short Holding Time Ratio", "threshold": 80, "unit": "% ratio", "description": "Triggers when more than the threshold of received funds are transferred out of the account within 30 minutes.", "active": True },
            { "id": "R-NET-1", "name": "Suspicious Component Connection", "threshold": 1, "unit": "hops", "description": "Triggers when a node has direct connection (shared device/IP/phone) to previously blocked/flagged fraud nodes.", "active": True },
            { "id": "R-VAL-1", "name": "High-Value Shell Transfer", "threshold": 100000, "unit": "INR", "description": "Triggers on a transfer exceeding threshold from/to newly registered corporate shell entities.", "active": True }
        ],
        "accounts": accounts,
        "transactions": transactions,
        "alerts": alerts,
        "cases": cases,
        "decisions": decisions,
        "auditLogs": audit_logs,
        "networks": networks
    }
    
    return db_out

def main():
    print("Generating expanded noisy reproducible synthetic dataset...")
    db = generate_db()
    
    # Save as JSON
    os.makedirs("data", exist_ok=True)
    with open("data/synthetic_db.json", "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)
    print("Saved: data/synthetic_db.json")
    
    # Save as JS seed file for the browser
    js_content = f"// Automatically generated expanded synthetic database seed\nwindow.MuleGuardExpandedDB = {json.dumps(db, indent=4, ensure_ascii=False)};\n"
    os.makedirs(os.path.join("frontend", "scripts"), exist_ok=True)
    with open(os.path.join("frontend", "scripts", "synthetic_db_expanded.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    print("Saved: frontend/scripts/synthetic_db_expanded.js")
    
    # Report class & scenario distributions
    total_accs = len(db["accounts"])
    mules = sum(1 for a in db["accounts"].values() if a["status"] != "Normal")
    legit = total_accs - mules
    
    print("\n--- Generation Statistics ---")
    print(f"Total Accounts:      {total_accs}")
    print(f"Total Transactions:  {len(db['transactions'])}")
    print(f"Legitimate Accounts: {legit}")
    print(f"Suspicious/Mules:    {mules}")
    
    # Group by scenario
    scenarios = {}
    for a in db["accounts"].values():
        s = a.get("scenario", "Unknown")
        scenarios[s] = scenarios.get(s, 0) + 1
    print("\nScenarios Breakdown:")
    for s, cnt in sorted(scenarios.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {s}: {cnt} accounts")

if __name__ == "__main__":
    main()
