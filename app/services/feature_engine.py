from collections import defaultdict
from datetime import timezone
import math

from app.db.database import get_connection


FEATURE_ORDER = [
    "txCount",
    "inTxCount",
    "outTxCount",
    "totalInAmount",
    "totalOutAmount",
    "uniqueCounterparties",
    "velocity",
    "avgTxAmount",
    "amountStdDev",
    "rapidHoldingRatio",
    "inOutRatio",
    "behavioralShift",
    "networkDegree",
    "inboundDegree",
    "outboundDegree",
    "isFanIn",
    "isFanOut",
    "sharedSuspiciousConnection",
    "totalDegree",
    "fanIn",
    "fanOut",
    "networkConcentration",
    "cycleParticipation",
    "multiHopConnectivity",
    "temporalProximity",
    "activityPattern",
]


def _to_utc(dt):
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _std_dev(values):
    if len(values) <= 1:
        return 0.0

    mean = sum(values) / len(values)

    variance = sum(
        (value - mean) ** 2
        for value in values
    ) / len(values)

    return math.sqrt(variance)


def load_analysis_data():
    """
    Load all required PostgreSQL data once.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    a.id,
                    a.status,
                    c.phone,
                    c.device_fingerprint,
                    c.ip_address
                FROM accounts a
                JOIN customers c
                    ON c.id = a.customer_id;
                """
            )

            account_rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    id,
                    sender_account_id,
                    receiver_account_id,
                    amount,
                    transaction_timestamp,
                    status
                FROM transactions
                ORDER BY transaction_timestamp;
                """
            )

            transaction_rows = cur.fetchall()

    accounts = {}

    for row in account_rows:
        accounts[row[0]] = {
            "id": row[0],
            "status": row[1],
            "phone": row[2],
            "device": row[3],
            "ip": row[4],
        }

    transactions = []

    for row in transaction_rows:
        transactions.append(
            {
                "id": row[0],
                "sender": row[1],
                "receiver": row[2],
                "amount": float(row[3]),
                "timestamp": _to_utc(row[4]),
                "status": row[5],
            }
        )

    return accounts, transactions


def build_indexes(accounts, transactions):
    """
    Pre-compute indexes so feature calculation does not
    repeatedly scan the entire database.
    """

    inbound = defaultdict(list)
    outbound = defaultdict(list)

    adjacency = defaultdict(set)

    for tx in transactions:

        sender = tx["sender"]
        receiver = tx["receiver"]

        if receiver:
            inbound[receiver].append(tx)

        if sender:
            outbound[sender].append(tx)

        if sender and receiver:
            adjacency[sender].add(receiver)

    suspicious_accounts = {
        account_id
        for account_id, account in accounts.items()
        if account["status"]
        in {
            "Blocked",
            "Flagged",
            "Critical",
        }
    }

    return (
        inbound,
        outbound,
        adjacency,
        suspicious_accounts,
    )


def _has_cycle(
    account_id,
    adjacency,
    max_depth=4,
):
    def search(current, depth, visited):

        if depth > max_depth:
            return False

        for neighbor in adjacency.get(current, set()):

            if neighbor == account_id and depth >= 2:
                return True

            if neighbor not in visited:

                visited.add(neighbor)

                if search(
                    neighbor,
                    depth + 1,
                    visited,
                ):
                    return True

                visited.remove(neighbor)

        return False

    return search(
        account_id,
        1,
        {account_id},
    )


def _multi_hop_connectivity(
    account_id,
    adjacency,
):
    direct_neighbors = set()

    for neighbor in adjacency.get(account_id, set()):
        direct_neighbors.add(neighbor)

    for node, neighbors in adjacency.items():

        if account_id in neighbors:
            direct_neighbors.add(node)

    two_hop_neighbors = set(direct_neighbors)

    for neighbor in direct_neighbors:

        for second_neighbor in adjacency.get(
            neighbor,
            set(),
        ):
            if second_neighbor != account_id:
                two_hop_neighbors.add(
                    second_neighbor
                )

        for node, neighbors in adjacency.items():
            if neighbor in neighbors and node != account_id:
                two_hop_neighbors.add(node)

    return len(two_hop_neighbors)


def calculate_account_features(
    account_id,
    accounts,
    transactions,
    indexes,
):
    """
    Calculate the exact 26-feature vector for one account
    using pre-loaded PostgreSQL data.
    """

    if account_id not in accounts:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    account = accounts[account_id]

    (
        inbound_index,
        outbound_index,
        adjacency,
        suspicious_accounts,
    ) = indexes

    inbound = inbound_index.get(
        account_id,
        [],
    )

    outbound = outbound_index.get(
        account_id,
        [],
    )

    all_transactions = inbound + outbound

    tx_count = len(all_transactions)

    in_tx_count = len(inbound)

    out_tx_count = len(outbound)

    total_in_amount = sum(
        tx["amount"]
        for tx in inbound
    )

    total_out_amount = sum(
        tx["amount"]
        for tx in outbound
    )

    counterparties = set()

    for tx in all_transactions:

        if (
            tx["sender"]
            and tx["sender"] != account_id
        ):
            counterparties.add(
                tx["sender"]
            )

        if (
            tx["receiver"]
            and tx["receiver"] != account_id
        ):
            counterparties.add(
                tx["receiver"]
            )

    unique_counterparties = len(
        counterparties
    )

    velocity = tx_count

    amounts = [
        tx["amount"]
        for tx in all_transactions
    ]

    avg_tx_amount = (
        sum(amounts) / len(amounts)
        if amounts
        else 0.0
    )

    amount_std_dev = _std_dev(
        amounts
    )

    if total_in_amount > 0:

        rapid_holding_ratio = min(
            100.0,
            (
                total_out_amount
                / total_in_amount
            )
            * 100.0,
        )

        in_out_ratio = (
            total_out_amount
            / total_in_amount
        )

    else:

        rapid_holding_ratio = 0.0
        in_out_ratio = 0.0

    # -----------------------------------------
    # Temporal features
    # -----------------------------------------

    behavioral_shift = 0.0
    activity_pattern = 0.0

    if all_transactions:

        latest_time = max(
            tx["timestamp"]
            for tx in all_transactions
        )

        recent_1h = sum(
            1
            for tx in all_transactions
            if (
                latest_time
                - tx["timestamp"]
            ).total_seconds()
            <= 3600
        )

        recent_2h = sum(
            1
            for tx in all_transactions
            if (
                latest_time
                - tx["timestamp"]
            ).total_seconds()
            <= 7200
        )

        behavioral_shift = (
            recent_1h / tx_count
        )

        activity_pattern = (
            recent_2h / tx_count
        )

    # -----------------------------------------
    # Network features
    # -----------------------------------------

    inbound_counterparties = {
        tx["sender"]
        for tx in inbound
        if (
            tx["sender"]
            and tx["sender"] != account_id
        )
    }

    outbound_counterparties = {
        tx["receiver"]
        for tx in outbound
        if (
            tx["receiver"]
            and tx["receiver"] != account_id
        )
    }

    inbound_degree = in_tx_count

    outbound_degree = out_tx_count

    network_degree = (
        inbound_degree
        + outbound_degree
    )

    is_fan_in = (
        1.0
        if len(inbound_counterparties) >= 3
        else 0.0
    )

    is_fan_out = (
        1.0
        if len(outbound_counterparties) >= 3
        else 0.0
    )

    # -----------------------------------------
    # Shared suspicious connection
    # -----------------------------------------

    shared_suspicious_connection = 0.0

    for other_id in suspicious_accounts:

        if other_id == account_id:
            continue

        other = accounts[other_id]

        if (
            account["phone"]
            == other["phone"]
            or account["device"]
            == other["device"]
            or account["ip"]
            == other["ip"]
        ):
            shared_suspicious_connection = 1.0
            break

    # -----------------------------------------
    # Network concentration
    # -----------------------------------------

    counterparty_volumes = defaultdict(
        float
    )

    for tx in all_transactions:

        if tx["sender"] == account_id:
            partner = tx["receiver"]
        else:
            partner = tx["sender"]

        if (
            partner
            and partner != account_id
        ):
            counterparty_volumes[
                partner
            ] += tx["amount"]

    total_volume = sum(
        counterparty_volumes.values()
    )

    network_concentration = 0.0

    if total_volume > 0:

        for volume in counterparty_volumes.values():

            share = (
                volume / total_volume
            )

            network_concentration += (
                share * share
            )

    # -----------------------------------------
    # Cycle
    # -----------------------------------------

    cycle_participation = (
        1.0
        if _has_cycle(
            account_id,
            adjacency,
        )
        else 0.0
    )

    # -----------------------------------------
    # Multi-hop
    # -----------------------------------------

    multi_hop_connectivity = (
        _multi_hop_connectivity(
            account_id,
            adjacency,
        )
    )

    # -----------------------------------------
    # Temporal proximity
    # -----------------------------------------

    temporal_proximity = 1440.0

    for in_tx in inbound:

        for out_tx in outbound:

            gap = (
                out_tx["timestamp"]
                - in_tx["timestamp"]
            ).total_seconds() / 60.0

            if gap >= 0:
                temporal_proximity = min(
                    temporal_proximity,
                    gap,
                )

    features = {
        "txCount": tx_count,
        "inTxCount": in_tx_count,
        "outTxCount": out_tx_count,
        "totalInAmount": total_in_amount,
        "totalOutAmount": total_out_amount,
        "uniqueCounterparties": unique_counterparties,
        "velocity": velocity,
        "avgTxAmount": avg_tx_amount,
        "amountStdDev": amount_std_dev,
        "rapidHoldingRatio": rapid_holding_ratio,
        "inOutRatio": in_out_ratio,
        "behavioralShift": behavioral_shift,
        "networkDegree": network_degree,
        "inboundDegree": inbound_degree,
        "outboundDegree": outbound_degree,
        "isFanIn": is_fan_in,
        "isFanOut": is_fan_out,
        "sharedSuspiciousConnection": shared_suspicious_connection,
        "totalDegree": network_degree,
        "fanIn": len(inbound_counterparties),
        "fanOut": len(outbound_counterparties),
        "networkConcentration": network_concentration,
        "cycleParticipation": cycle_participation,
        "multiHopConnectivity": multi_hop_connectivity,
        "temporalProximity": temporal_proximity,
        "activityPattern": activity_pattern,
    }

    return {
        "account_id": account_id,
        "status": account["status"],
        "features": features,
        "feature_vector": [
            features[name]
            for name in FEATURE_ORDER
        ],
    }


def calculate_all_features():
    """
    Calculate features for every account using one
    PostgreSQL data load.
    """

    accounts, transactions = (
        load_analysis_data()
    )

    indexes = build_indexes(
        accounts,
        transactions,
    )

    results = []

    for account_id in accounts:

        result = calculate_account_features(
            account_id,
            accounts,
            transactions,
            indexes,
        )

        results.append(result)

    return results

def calculate_account_features_from_db(account_id: str):
    accounts, transactions = load_analysis_data()
    indexes = build_indexes(accounts, transactions)

    return calculate_account_features(
        account_id,
        accounts,
        transactions,
        indexes,
    )