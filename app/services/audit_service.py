"""
MuleGuard Centralized Operational & Security Audit Service
Queries real PostgreSQL application (audit_logs) and security (auth_audit_log) audit trails.
Enforces bounded pagination, server-side filtering, data sanitization, and summary metrics.
Strictly read-only; does NOT write audit logs on query or dashboard polling.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.db.database import get_connection

SENSITIVE_KEYS = {
    "password", "password_hash", "token", "session_token", "session_id", "secret",
    "private_key", "salt", "biometric", "probe_vector", "face_vector", "embedding",
    "template", "challenge_token", "authorization", "auth_header", "credential",
    "credentials", "db_password"
}


def sanitize_details(obj: Any) -> Any:
    """Recursively redacts sensitive keys from audit details payloads."""
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            key_lower = str(k).lower()
            if any(s in key_lower for s in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, (dict, list)):
                sanitized[k] = sanitize_details(v)
            else:
                sanitized[k] = v
        return sanitized
    elif isinstance(obj, list):
        return [sanitize_details(item) for item in obj]
    return obj


def get_audit_summary() -> Dict[str, int]:
    """Calculates real audit summary counters directly from PostgreSQL."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Total events across both application & auth audit tables
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM audit_logs) + (SELECT COUNT(*) FROM auth_audit_log);
            """)
            total_events = cur.fetchone()[0]

            # 2. Events today (UTC)
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM audit_logs WHERE created_at >= CURRENT_DATE)
                    +
                    (SELECT COUNT(*) FROM auth_audit_log WHERE event_timestamp >= CURRENT_DATE);
            """)
            events_today = cur.fetchone()[0]

            # 3. Authentication events
            cur.execute("""
                SELECT COUNT(*) FROM auth_audit_log 
                WHERE event_type IN (
                    'STAGE1_SUCCESS', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 
                    'FACE_VERIFICATION_SUCCESS', 'FACE_VERIFICATION_FAILED', 
                    'FACE_ENROLLMENT_SUCCESS', 'FACE_ENROLLMENT_FAILED'
                );
            """)
            auth_events = cur.fetchone()[0]

            # 4. Security events
            cur.execute("""
                SELECT COUNT(*) FROM auth_audit_log 
                WHERE event_type IN (
                    'PAD_ATTACK_DETECTED', 'LIVENESS_FAILED', 'RATE_LIMIT_EXCEEDED', 'ACCOUNT_LOCKED'
                );
            """)
            sec_events = cur.fetchone()[0]

            # 5. Transaction events
            cur.execute("""
                SELECT COUNT(*) FROM audit_logs 
                WHERE action ILIKE '%%TRANSACTION%%' OR entity_type = 'transaction';
            """)
            tx_events = cur.fetchone()[0]

            # 6. ML / Analysis events
            cur.execute("""
                SELECT COUNT(*) FROM audit_logs 
                WHERE action ILIKE '%%ML%%' OR action ILIKE '%%GRAPH%%' OR action ILIKE '%%ANALYSIS%%';
            """)
            ml_events = cur.fetchone()[0]

    return {
        "total_events": total_events,
        "events_today": events_today,
        "authentication_events": auth_events,
        "security_events": sec_events,
        "transaction_events": tx_events,
        "ml_analysis_events": ml_events,
    }


def query_internal_audit_logs(
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    account_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a bounded, server-side filtered query over unified PostgreSQL audit logs.
    Limit is safely constrained to between 1 and 500 records.
    """
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)

    base_cte = """
        WITH unified_audit AS (
            SELECT 
                'app_' || id::text AS audit_id,
                created_at AS timestamp,
                action,
                entity_type,
                entity_id,
                account_id,
                COALESCE(details->>'actor', 'SYSTEM') AS actor,
                details,
                CASE 
                    WHEN action ILIKE '%%PAD_ATTACK%%' OR action ILIKE '%%LIVENESS%%' OR action ILIKE '%%RATE_LIMIT%%' OR action ILIKE '%%ACCOUNT_LOCKED%%' THEN 'SECURITY'
                    WHEN action ILIKE '%%LOGIN%%' OR action ILIKE '%%LOGOUT%%' OR action ILIKE '%%STAGE1%%' OR action ILIKE '%%FACE_%%' THEN 'AUTHENTICATION'
                    WHEN action ILIKE '%%TRANSACTION%%' OR entity_type = 'transaction' THEN 'TRANSACTION'
                    WHEN action ILIKE '%%ALERT%%' OR entity_type = 'alert' THEN 'ALERT'
                    WHEN action ILIKE '%%CASE%%' OR entity_type = 'case' THEN 'CASE'
                    WHEN action ILIKE '%%WATCHLIST%%' OR entity_type = 'watchlist' THEN 'WATCHLIST'
                    WHEN action ILIKE '%%DECISION%%' OR entity_type = 'decision' THEN 'DECISION'
                    WHEN action ILIKE '%%RULE%%' OR entity_type = 'rule' THEN 'RULE'
                    WHEN action ILIKE '%%ML%%' OR action ILIKE '%%MODEL%%' THEN 'ML'
                    WHEN action ILIKE '%%GRAPH%%' THEN 'GRAPH'
                    ELSE 'SYSTEM'
                END AS category
            FROM audit_logs

            UNION ALL

            SELECT 
                'auth_' || id::text AS audit_id,
                event_timestamp AS timestamp,
                event_type AS action,
                'auth' AS entity_type,
                COALESCE(user_id, employee_id, '') AS entity_id,
                NULL AS account_id,
                COALESCE(employee_id, user_id, 'Anonymous') AS actor,
                jsonb_build_object(
                    'outcome', outcome,
                    'ip_address', ip_address,
                    'failure_reason', failure_reason,
                    'details', details
                ) AS details,
                CASE 
                    WHEN event_type IN ('PAD_ATTACK_DETECTED', 'LIVENESS_FAILED', 'RATE_LIMIT_EXCEEDED', 'ACCOUNT_LOCKED') THEN 'SECURITY'
                    ELSE 'AUTHENTICATION'
                END AS category
            FROM auth_audit_log
        )
    """

    where_clauses = ["1=1"]
    params: List[Any] = []

    if action:
        where_clauses.append("action ILIKE %s")
        params.append(f"%{action}%")

    if entity_type:
        where_clauses.append("entity_type ILIKE %s")
        params.append(f"%{entity_type}%")

    if entity_id:
        where_clauses.append("entity_id ILIKE %s")
        params.append(f"%{entity_id}%")

    if account_id:
        where_clauses.append("account_id ILIKE %s")
        params.append(f"%{account_id}%")

    if category and category.upper() != "ALL":
        where_clauses.append("category = %s")
        params.append(category.upper())

    if search:
        where_clauses.append("""
            (
                audit_id ILIKE %s OR
                action ILIKE %s OR
                actor ILIKE %s OR
                entity_id ILIKE %s OR
                account_id ILIKE %s OR
                details::text ILIKE %s
            )
        """)
        search_pattern = f"%{search}%"
        params.extend([search_pattern] * 6)

    if date_from:
        where_clauses.append("timestamp >= %s")
        params.append(date_from)

    if date_to:
        where_clauses.append("timestamp <= %s")
        params.append(date_to)

    where_sql = " AND ".join(where_clauses)

    count_sql = f"{base_cte} SELECT COUNT(*) FROM unified_audit WHERE {where_sql};"
    items_sql = f"""
        {base_cte}
        SELECT 
            audit_id,
            timestamp,
            action,
            entity_type,
            entity_id,
            account_id,
            actor,
            details,
            category
        FROM unified_audit
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT %s OFFSET %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Count matching rows
            cur.execute(count_sql, tuple(params))
            total_matching = cur.fetchone()[0]

            # 2. Fetch page items
            page_params = list(params) + [safe_limit, safe_offset]
            cur.execute(items_sql, tuple(page_params))
            rows = cur.fetchall()

    items = []
    for r in rows:
        ts = r[1]
        iso_ts = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        items.append({
            "id": r[0],
            "timestamp": iso_ts,
            "action": r[2],
            "entity_type": r[3],
            "entity_id": r[4],
            "account_id": r[5],
            "actor": r[6],
            "details": sanitize_details(r[7]),
            "category": r[8],
        })

    summary = get_audit_summary()

    return {
        "status": "Healthy",
        "retention_policy": "Not configured",
        "summary": summary,
        "pagination": {
            "limit": safe_limit,
            "offset": safe_offset,
            "total": total_matching,
            "has_more": (safe_offset + len(items)) < total_matching,
        },
        "items": items,
    }
