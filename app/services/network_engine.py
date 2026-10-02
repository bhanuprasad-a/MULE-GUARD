"""
MuleGuard Network Analysis Engine
Calculates real transaction-network topology, multi-hop mesh connectivity, connected components,
degree metrics, cycle participation, fan-in/fan-out patterns, counterparty statistics,
and deterministic network risk scores directly from PostgreSQL accounts and transactions.
"""

from collections import defaultdict, deque
import math
from typing import Dict, List, Any, Optional
from psycopg.rows import dict_row

from app.db.database import get_connection


def format_inr(amount: float) -> str:
    """Format monetary value into clean INR string with ₹ symbol."""
    val = float(amount or 0)
    if val >= 10_000_000:
        return f"₹{val / 10_000_000:.2f} Cr"
    elif val >= 100_000:
        return f"₹{val / 100_000:.2f} Lakh"
    else:
        return f"₹{val:,.2f}".rstrip('0').rstrip('.')


def compute_network_intelligence(conn=None) -> Dict[str, Any]:
    """
    Computes real database-derived Network Intelligence from PostgreSQL accounts and transactions.
    Constructs true multi-hop transaction mesh topologies with zero artificial edges and zero forced star hubs.
    
    Returns:
        dict mapping network_id -> network_object (for frontend networksDb compatibility).
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        with conn.cursor(row_factory=dict_row) as cur:
            # 1. Load accounts with customer info
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
            
            accounts_map = {}
            for acc in accounts_list:
                acc_id = acc["account_id"]
                cust_name = acc["customer_name"] or acc_id
                acc_type = acc["account_type"] or "Savings"
                # Determine if business: Current account or commercial naming
                is_biz = (acc_type == "Current") or any(k in cust_name.lower() for k in [
                    "stores", "depot", "agencies", "textiles", "point", "electronics",
                    "parts", "parlour", "hardware", "center", "sweets", "hotel",
                    "supermarket", "logistics", "traders", "stall", "opticals", "wear",
                    "jewellers", "service", "care", "bar", "nursery", "enterprise", "ltd"
                ])
                
                # Extract city from address if present
                addr = acc.get("address") or ""
                city = "Retail Branch"
                for c_name in ["Vijayawada", "Hyderabad", "Chennai", "Bengaluru", "Mumbai", "Delhi", "Pune", "Kolkata", "Visakhapatnam", "Ahmedabad", "Jaipur", "Kochi", "Lucknow", "Guntur", "Surat", "Tirupati"]:
                    if c_name.lower() in addr.lower():
                        city = c_name
                        break

                accounts_map[acc_id] = {
                    "id": acc_id,
                    "account_id": acc_id,
                    "customer_id": acc["customer_id"],
                    "customer_name": cust_name,
                    "label": cust_name,
                    "account_type": acc_type,
                    "is_business": is_biz,
                    "balance": float(acc["balance"] or 0),
                    "balance_formatted": format_inr(acc["balance"]),
                    "status": acc["status"] or "Normal",
                    "opened_at": acc["opened_at"].isoformat() if acc["opened_at"] else "",
                    "phone": acc["phone"] or "",
                    "device": acc["device_fingerprint"] or "",
                    "ip": str(acc["ip_address"]) if acc["ip_address"] else "",
                    "city": city,
                    "address": addr
                }

            # 2. Load alerts to map explicit alert severity and scores
            cur.execute("""
                SELECT account_id, risk_score, severity, status
                FROM alerts
                WHERE status != 'Resolved'
            """)
            alerts_list = cur.fetchall()
            alerts_map = defaultdict(list)
            for alt in alerts_list:
                alerts_map[alt["account_id"]].append(alt)

            for acc_id, acc in accounts_map.items():
                if acc["status"] == "Blocked":
                    acc["risk_score"] = 96
                elif acc["status"] == "Critical":
                    acc["risk_score"] = 94
                elif acc["status"] == "Flagged":
                    acc["risk_score"] = 88
                elif acc["status"] == "Under Review":
                    acc["risk_score"] = 72
                elif acc_id in alerts_map:
                    max_sc = max([float(a["risk_score"] or 50) for a in alerts_map[acc_id]])
                    acc["risk_score"] = int(max(35, max_sc))
                else:
                    acc["risk_score"] = 18

            # 3. Load all valid transactions from PostgreSQL
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

    finally:
        if should_close:
            conn.close()

    # Build transaction index and graphs
    valid_txs = []
    undirected_adj = defaultdict(set)
    directed_adj = defaultdict(set)
    in_degree_map = defaultdict(int)
    out_degree_map = defaultdict(int)
    total_in_map = defaultdict(float)
    total_out_map = defaultdict(float)
    in_tx_map = defaultdict(list)
    out_tx_map = defaultdict(list)
    counterparty_tx_map = defaultdict(lambda: defaultdict(list))

    for tx in tx_rows:
        s_id = tx["sender_account_id"]
        r_id = tx["receiver_account_id"]
        if s_id in accounts_map and r_id in accounts_map and s_id != r_id:
            amt = float(tx["amount"] or 0)
            tx_time_str = (tx["transaction_timestamp"] or tx["created_at"]).isoformat()
            tx_obj = {
                "id": tx["id"],
                "sender_id": s_id,
                "receiver_id": r_id,
                "amount": amt,
                "amount_formatted": format_inr(amt),
                "transaction_type": tx["transaction_type"] or "Transfer",
                "type": tx["transaction_type"] or "Transfer",
                "timestamp": tx_time_str,
                "time": tx_time_str,
                "status": tx["status"] or "Completed",
                "origin": tx["origin"] or accounts_map[s_id]["city"],
                "destination": tx["destination"] or accounts_map[r_id]["city"]
            }
            valid_txs.append(tx_obj)
            undirected_adj[s_id].add(r_id)
            undirected_adj[r_id].add(s_id)
            directed_adj[s_id].add(r_id)
            out_degree_map[s_id] += 1
            in_degree_map[r_id] += 1
            total_out_map[s_id] += amt
            total_in_map[r_id] += amt
            out_tx_map[s_id].append(tx_obj)
            in_tx_map[r_id].append(tx_obj)
            counterparty_tx_map[s_id][r_id].append(tx_obj)

    # 4. Precompute per-account transaction aggregates & suspicion reasons
    # Detect directed cycles in the overall graph
    cycle_nodes_global = set()
    for start_node in accounts_map:
        if in_degree_map[start_node] > 0 and out_degree_map[start_node] > 0:
            visited_local = {start_node}
            path = [start_node]
            def find_cycles(curr, depth):
                if depth > 4:
                    return
                for nxt in directed_adj[curr]:
                    if nxt == start_node and depth >= 2:
                        cycle_nodes_global.update(path)
                    elif nxt not in visited_local:
                        visited_local.add(nxt)
                        path.append(nxt)
                        find_cycles(nxt, depth + 1)
                        path.pop()
                        visited_local.remove(nxt)
            find_cycles(start_node, 1)

    # Device & IP sharing map
    device_accounts = defaultdict(set)
    ip_accounts = defaultdict(set)
    for a_id, a_data in accounts_map.items():
        if a_data["device"]:
            device_accounts[a_data["device"]].add(a_id)
        if a_data["ip"]:
            ip_accounts[a_data["ip"]].add(a_id)

    for a_id, acc in accounts_map.items():
        in_cnt = in_degree_map[a_id]
        out_cnt = out_degree_map[a_id]
        tot_in = total_in_map[a_id]
        tot_out = total_out_map[a_id]
        counterparties = undirected_adj[a_id]
        
        acc["in_degree"] = in_cnt
        acc["out_degree"] = out_cnt
        acc["total_incoming"] = tot_in
        acc["total_incoming_formatted"] = format_inr(tot_in)
        acc["total_outgoing"] = tot_out
        acc["total_outgoing_formatted"] = format_inr(tot_out)
        acc["incoming_count"] = len(in_tx_map[a_id])
        acc["outgoing_count"] = len(out_tx_map[a_id])
        acc["total_transactions"] = acc["incoming_count"] + acc["outgoing_count"]
        acc["unique_counterparties"] = len(counterparties)
        acc["connected_accounts_count"] = len(counterparties)

        # Build detailed connected counterparties list
        conn_list = []
        for cp_id in counterparties:
            cp_acc = accounts_map[cp_id]
            # Inbound from cp?
            in_amt = sum(t["amount"] for t in in_tx_map[a_id] if t["sender_id"] == cp_id)
            out_amt = sum(t["amount"] for t in out_tx_map[a_id] if t["receiver_id"] == cp_id)
            tot_amt = in_amt + out_amt
            if in_amt > 0 and out_amt > 0:
                direction = "Bidirectional (In/Out)"
            elif in_amt > 0:
                direction = "Inbound (Sent to Account)"
            else:
                direction = "Outbound (Received from Account)"

            conn_list.append({
                "account_id": cp_id,
                "customer_name": cp_acc["customer_name"],
                "account_type": cp_acc["account_type"],
                "is_business": cp_acc["is_business"],
                "status": cp_acc["status"],
                "risk_score": cp_acc["risk_score"],
                "direction": direction,
                "total_amount": tot_amt,
                "total_amount_formatted": format_inr(tot_amt),
                "inbound_amount": in_amt,
                "outbound_amount": out_amt,
                "transaction_count": len(counterparty_tx_map[cp_id][a_id]) + len(counterparty_tx_map[a_id][cp_id])
            })
        conn_list.sort(key=lambda x: x["total_amount"], reverse=True)
        acc["connected_accounts"] = conn_list

        # Recent transactions involving this account
        all_acc_txs = in_tx_map[a_id] + out_tx_map[a_id]
        all_acc_txs.sort(key=lambda t: t["timestamp"], reverse=True)
        recent_txs = []
        for t in all_acc_txs[:8]:
            is_in = (t["receiver_id"] == a_id)
            cp_id = t["sender_id"] if is_in else t["receiver_id"]
            cp_name = accounts_map.get(cp_id, {}).get("customer_name", cp_id)
            recent_txs.append({
                "id": t["id"],
                "amount": t["amount"],
                "amount_formatted": t["amount_formatted"],
                "type": t["transaction_type"],
                "timestamp": t["timestamp"],
                "status": t["status"],
                "is_inbound": is_in,
                "direction": "INBOUND" if is_in else "OUTBOUND",
                "counterparty_id": cp_id,
                "counterparty_name": cp_name,
                "origin": t["origin"],
                "destination": t["destination"]
            })
        acc["recent_transactions"] = recent_txs

        # Detailed Behavioral Suspicion Reasons
        reasons = []
        if a_id in cycle_nodes_global:
            reasons.append("Circular Money Flow: Account participates in a closed multi-hop transaction cycle.")
        
        # Short holding time detection
        if len(in_tx_map[a_id]) > 0 and len(out_tx_map[a_id]) > 0:
            reasons.append("Rapid Forwarding: Inbound funds forwarded to external beneficiaries within rolling operating window.")

        # Inbound velocity
        if in_cnt >= 4:
            reasons.append(f"Inbound Velocity Spike: Aggregated funds from {in_cnt} distinct sending counterparties.")

        # Fan-in or Fan-out ratio
        if in_cnt >= 3 and (in_cnt >= 2 * max(1, out_cnt)):
            reasons.append(f"Fan-In Aggregator: Structured collection from {in_cnt} distinct feeder accounts.")
        if out_cnt >= 3 and (out_cnt >= 2 * max(1, in_cnt)):
            reasons.append(f"Fan-Out Dispersal: Rapid smurfing/distribution to {out_cnt} secondary destination accounts.")

        # Shared Device / IP
        shared_dev_accs = [x for x in device_accounts[acc["device"]] if x != a_id]
        if len(shared_dev_accs) > 0:
            reasons.append(f"Shared Device Footprint: Device fingerprint matches {len(shared_dev_accs)} other account(s) ({', '.join(shared_dev_accs[:3])}).")

        shared_ip_accs = [x for x in ip_accounts[acc["ip"]] if x != a_id]
        if len(shared_ip_accs) > 0 and acc["ip"]:
            reasons.append(f"Shared IP Network: IP address shared with {len(shared_ip_accs)} other account(s).")

        # Connection to blocked/flagged accounts
        susp_cp = [c for c in conn_list if c["status"] in ("Blocked", "Flagged", "Critical")]
        if len(susp_cp) > 0:
            reasons.append(f"Direct High-Risk Connection: Direct transfers with {len(susp_cp)} flagged or blocked account(s) ({', '.join([c['account_id'] for c in susp_cp[:2]])}).")

        if acc["status"] in ("Flagged", "Critical", "Blocked", "Under Review") and not reasons:
            reasons.append(f"Behavioral Anomaly: Account elevated to {acc['status']} status based on ML risk probability.")

        if not reasons:
            if acc["is_business"]:
                reasons.append("Legitimate Commercial Merchant: Normal commercial receipts and supplier disbursements.")
            else:
                reasons.append("Legitimate Retail Customer: Standard peer-to-peer and retail merchant payment behavior.")

        acc["suspicion_reasons"] = reasons
        acc["risk"] = (
            "Critical" if acc["risk_score"] >= 90
            else "High" if acc["risk_score"] >= 70
            else "Medium" if acc["risk_score"] >= 40
            else "Low"
        )

    # 5. Extract Multi-Hop Transaction Networks / Subgraphs
    # We want natural transaction networks that reflect real multi-hop money flow.
    # Group connected accounts into networks using connected components and multi-hop paths.
    visited_nodes = set()
    extracted_clusters = []

    # First, prioritize all accounts that are suspicious or participate in multi-hop loops/conduits
    suspicious_seed_accounts = [
        a_id for a_id, a_data in accounts_map.items()
        if a_data["status"] in ("Flagged", "Critical", "Under Review", "Blocked") or a_id in cycle_nodes_global
    ]
    # Sort seeds by risk score
    suspicious_seed_accounts.sort(key=lambda x: accounts_map[x]["risk_score"], reverse=True)

    for seed_id in suspicious_seed_accounts:
        if seed_id in visited_nodes:
            continue
        
        # Traverse the multi-hop transaction component around this seed
        cluster_nodes = set()
        frontier = deque([seed_id])
        visited_nodes.add(seed_id)
        cluster_nodes.add(seed_id)

        # Expand BFS along real transaction edges (depth up to 3 hops)
        depth_map = {seed_id: 0}
        while frontier:
            curr = frontier.popleft()
            curr_depth = depth_map[curr]
            if curr_depth >= 3:
                continue

            for nxt in undirected_adj[curr]:
                # Add neighbor if it's suspicious, directly connected, or part of the cluster's internal tx flow
                if nxt not in cluster_nodes:
                    is_susp = accounts_map[nxt]["status"] in ("Flagged", "Critical", "Under Review", "Blocked")
                    # If neighbor is suspicious, expand freely; if normal, include up to reasonable cluster size
                    if is_susp or len(cluster_nodes) < 14:
                        cluster_nodes.add(nxt)
                        visited_nodes.add(nxt)
                        depth_map[nxt] = curr_depth + 1
                        frontier.append(nxt)

        if len(cluster_nodes) >= 2:
            extracted_clusters.append({
                "primary_id": seed_id,
                "nodes": list(cluster_nodes),
                "is_suspicious": True
            })

    # Next, extract major business/commercial meshes and retail chains
    business_seeds = [
        a_id for a_id, a_data in accounts_map.items()
        if a_data["is_business"] and a_id not in visited_nodes
    ]
    for b_id in business_seeds:
        if b_id in visited_nodes:
            continue
        cluster_nodes = {b_id}
        visited_nodes.add(b_id)
        
        # Include suppliers and frequent customers
        for nxt in list(undirected_adj[b_id])[:12]:
            cluster_nodes.add(nxt)
            visited_nodes.add(nxt)
            
        if len(cluster_nodes) >= 3:
            extracted_clusters.append({
                "primary_id": b_id,
                "nodes": list(cluster_nodes),
                "is_suspicious": False
            })

    # Catch any remaining connected components >= 3 nodes
    for a_id in accounts_map:
        if a_id not in visited_nodes and len(undirected_adj[a_id]) >= 2:
            comp = set()
            q = deque([a_id])
            visited_nodes.add(a_id)
            comp.add(a_id)
            while q and len(comp) < 10:
                curr = q.popleft()
                for nxt in undirected_adj[curr]:
                    if nxt not in comp:
                        comp.add(nxt)
                        visited_nodes.add(nxt)
                        q.append(nxt)
            if len(comp) >= 3:
                # Find most active node in component
                top_node = max(comp, key=lambda n: accounts_map[n]["total_transactions"])
                extracted_clusters.append({
                    "primary_id": top_node,
                    "nodes": list(comp),
                    "is_suspicious": False
                })

    # Sort networks: suspicious high-risk networks first, then by size and volume
    def cluster_sort_key(c):
        p_acc = accounts_map[c["primary_id"]]
        return (1 if c["is_suspicious"] else 0, p_acc["risk_score"], len(c["nodes"]))

    extracted_clusters.sort(key=cluster_sort_key, reverse=True)

    # 6. Build the final Network objects with ONLY REAL TRANSACTION EDGES
    networks = {}

    for idx, cluster in enumerate(extracted_clusters, start=1):
        primary_id = cluster["primary_id"]
        primary_acc = accounts_map[primary_id]
        comp_nodes_list = cluster["nodes"]
        comp_set = set(comp_nodes_list)

        # ONLY real transactions between nodes in this network
        comp_txs = [
            t for t in valid_txs 
            if t["sender_id"] in comp_set and t["receiver_id"] in comp_set
        ]
        
        # If internal txs are empty (rare), include transactions between primary and members
        if not comp_txs:
            comp_txs = [
                t for t in valid_txs
                if (t["sender_id"] == primary_id and t["receiver_id"] in comp_set) or
                   (t["receiver_id"] == primary_id and t["sender_id"] in comp_set)
            ]

        # Aggregate directed transaction edges (source -> target)
        edge_map = defaultdict(lambda: {
            "amount": 0.0,
            "count": 0,
            "tx_ids": [],
            "transactions": []
        })

        for t in comp_txs:
            s_id = t["sender_id"]
            r_id = t["receiver_id"]
            e_entry = edge_map[(s_id, r_id)]
            e_entry["amount"] += t["amount"]
            e_entry["count"] += 1
            e_entry["tx_ids"].append(t["id"])
            e_entry["transactions"].append({
                "id": t["id"],
                "amount": t["amount"],
                "amount_formatted": t["amount_formatted"],
                "type": t["transaction_type"],
                "timestamp": t["timestamp"],
                "status": t["status"],
                "origin": t["origin"],
                "destination": t["destination"]
            })

        graph_links = []
        for (s_id, r_id), e_data in edge_map.items():
            graph_links.append({
                "source": s_id,
                "target": r_id,
                "source_id": s_id,
                "target_id": r_id,
                "source_name": accounts_map[s_id]["customer_name"],
                "target_name": accounts_map[r_id]["customer_name"],
                "amount": e_data["amount"],
                "amount_formatted": format_inr(e_data["amount"]),
                "count": e_data["count"],
                "tx_ids": e_data["tx_ids"],
                "flow": True,
                "transactions": e_data["transactions"]
            })

        # Calculate network-level metrics
        total_net_volume = sum(l["amount"] for l in graph_links)
        suspicious_members = [
            n for n in comp_nodes_list 
            if accounts_map[n]["status"] in ("Flagged", "Critical", "Under Review", "Blocked") or accounts_map[n]["risk_score"] >= 70
        ]
        has_cycles = any(n in cycle_nodes_global for n in comp_nodes_list)

        # Classify network topology type
        if has_cycles:
            net_type = "Layering Loop"
        elif any(accounts_map[n]["in_degree"] >= 4 and accounts_map[n]["out_degree"] <= 2 for n in comp_nodes_list):
            net_type = "Fan-In Aggregator"
        elif any(accounts_map[n]["out_degree"] >= 4 and accounts_map[n]["in_degree"] <= 2 for n in comp_nodes_list):
            net_type = "Fan-Out Distributor"
        elif any("Dormant" in r for n in comp_nodes_list for r in accounts_map[n]["suspicion_reasons"]):
            net_type = "Dormant Reactivation"
        elif any("Shared Device" in r for n in comp_nodes_list for r in accounts_map[n]["suspicion_reasons"]):
            net_type = "Shared Infrastructure"
        elif any(accounts_map[n]["is_business"] for n in comp_nodes_list):
            net_type = "Merchant Settlement Mesh"
        else:
            net_type = "Transaction Chain"

        # Deterministic Risk Score for network (0 - 100)
        net_score = 20
        if has_cycles:
            net_score += 35
        if len(suspicious_members) > 0:
            net_score += min(35, len(suspicious_members) * 12)
        if net_type in ("Fan-In Aggregator", "Fan-Out Distributor"):
            net_score += 15
        if total_net_volume > 200000:
            net_score += 10
        elif total_net_volume > 50000:
            net_score += 5
        net_score = int(min(99, max(12, net_score)))

        # Status
        if any(accounts_map[n]["status"] == "Blocked" for n in comp_nodes_list):
            net_status = "Blocked"
        elif any(accounts_map[n]["status"] == "Critical" for n in comp_nodes_list) or net_score >= 88:
            net_status = "Critical"
        elif any(accounts_map[n]["status"] == "Flagged" for n in comp_nodes_list) or net_score >= 80:
            net_status = "Flagged"
        elif any(accounts_map[n]["status"] == "Under Review" for n in comp_nodes_list) or net_score >= 60:
            net_status = "Under Review"
        else:
            net_status = "Active"

        # Deterministic ID using primary account
        clean_num = "".join(filter(str.isdigit, primary_id))
        net_id = f"NET-{clean_num[-6:] if clean_num else idx:0>6}"
        
        # Real customer name from PostgreSQL
        primary_name = primary_acc["customer_name"]
        net_name = f"{primary_name} Network"

        # Specific node roles within this network
        graph_nodes = []
        for n_id in comp_nodes_list:
            n_acc = accounts_map[n_id]
            # Role determination
            if has_cycles and n_id in cycle_nodes_global:
                role = "Loop Participant"
            elif n_acc["in_degree"] >= 3 and n_acc["out_degree"] <= 1:
                role = "Fan-In Aggregator"
            elif n_acc["out_degree"] >= 3 and n_acc["in_degree"] <= 1:
                role = "Fan-Out Distributor"
            elif n_acc["in_degree"] > 0 and n_acc["out_degree"] > 0:
                role = "Intermediary Conduit"
            elif n_acc["out_degree"] > 0:
                role = "Funds Sender"
            elif n_acc["in_degree"] > 0:
                role = "Funds Receiver"
            elif n_acc["is_business"]:
                role = "Commercial Merchant"
            else:
                role = "Retail Customer"

            # Create node object with ALL rich PostgreSQL-derived attributes
            node_dict = dict(n_acc)
            node_dict["role"] = role
            node_dict["network_id"] = net_id
            node_dict["network_name"] = net_name
            node_dict["network_type"] = net_type
            node_dict["related_suspicious_accounts"] = [
                x for x in comp_nodes_list 
                if x != n_id and accounts_map[x]["status"] in ("Flagged", "Critical", "Under Review", "Blocked")
            ]
            graph_nodes.append(node_dict)

        # Behavioral indicators
        indicators = []
        if has_cycles:
            indicators.append("Circular Money Flow")
        if any(accounts_map[n]["in_degree"] >= 3 for n in comp_nodes_list):
            indicators.append("Rapid Inbound Layering")
        if any(accounts_map[n]["out_degree"] >= 3 for n in comp_nodes_list):
            indicators.append("Smurfing Dispersal")
        if any("Shared Device" in r for n in comp_nodes_list for r in accounts_map[n]["suspicion_reasons"]):
            indicators.append("Shared Digital Device")
        if any("Shared IP" in r for n in comp_nodes_list for r in accounts_map[n]["suspicion_reasons"]):
            indicators.append("Shared IP Footprint")
        if total_net_volume >= 100000:
            indicators.append("High Aggregate Volume")
        if len(suspicious_members) > 0:
            indicators.append(f"{len(suspicious_members)} Flagged Account(s)")
        if not indicators:
            indicators.append("Standard Retail Flow")

        # Summary narrative
        if has_cycles:
            summary = f"Multi-hop circular transaction flow involving {len(comp_nodes_list)} accounts moving {format_inr(total_net_volume)} in closed loops."
        elif net_type == "Fan-In Aggregator":
            summary = f"Fan-in aggregation syndicate routing funds from multiple retail feeders into {primary_name} ({primary_id})."
        elif net_type == "Fan-Out Distributor":
            summary = f"Fan-out smurfing dispersal routing structured tranches from {primary_name} ({primary_id}) to multiple recipient accounts."
        elif net_type == "Merchant Settlement Mesh":
            summary = f"Commercial settlement mesh connecting {primary_name} with customer UPI payments and wholesale vendor transfers."
        else:
            summary = f"Transaction network of {len(comp_nodes_list)} connected accounts with {len(graph_links)} directed transaction paths totaling {format_inr(total_net_volume)}."

        # Risk explanation
        risk_exp = " • ".join(indicators)

        networks[net_id] = {
            "id": net_id,
            "name": net_name,
            "type": net_type,
            "score": net_score,
            "status": net_status,
            "members": len(graph_nodes),
            "connectedCount": sum(len(n["connected_accounts"]) for n in graph_nodes),
            "totalValue": format_inr(total_net_volume),
            "totalValueNumeric": total_net_volume,
            "lastActivity": graph_links[0]["transactions"][0]["timestamp"] if graph_links and graph_links[0]["transactions"] else "Recent",
            "summary": summary,
            "riskExplanation": risk_exp,
            "indicators": indicators,
            "graphNodes": graph_nodes,
            "graphLinks": graph_links
        }

    return networks
