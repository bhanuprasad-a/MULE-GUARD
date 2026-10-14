"""
MuleGuard Internal Operations API Router
Endpoints for internal team administration, telemetry, and system health monitoring.
Protected by RBAC dependency require_role(["internal_team"]).
"""

from fastapi import APIRouter, Depends
from app.api.auth import require_role
from app.services.health_service import get_system_health, get_ml_health
from app.services.rule_engine import get_detection_rules_report
from app.services.network_engine import get_graph_health_report, analyze_graph_topology

router = APIRouter(
    prefix="/api/v1/internal",
    tags=["Internal Operations"],
    dependencies=[Depends(require_role(["internal_team"]))],
)


@router.get("/system-health")
def read_system_health():
    """
    Returns real-time backend telemetry:
    - API Gateway responsiveness and latency
    - PostgreSQL connection status and connection pool usage
    - MuleGuard XGBoost ML model loading, 26-feature validation, and inference readiness
    - PostgreSQL graph/network topology accessibility
    - Truthful Process Uptime
    - Real recent heartbeat event logs
    """
    return get_system_health()


@router.get("/ml-health")
def read_ml_health():
    """
    Returns real-time ML model operations and monitoring telemetry:
    - Production model status (loaded/type/path/objective)
    - Architecture details: 80 trees, 26 features compatibility
    - Safe operational smoke test with live latency
    - 26-feature schema validation (finite, missing check)
    - Real in-process inference telemetry (counts, avg/latest latency)
    - Live risk distribution
    - Operational decision and alert tier thresholds
    """
    return get_ml_health()


@router.get("/detection-rules")
def read_detection_rules():
    """
    Returns real-time detection rule operational and telemetry report:
    - 6 active MuleGuard detection rules (R-VEL-1, R-AGG-1, R-DIST-1, R-HOLD-1, R-CIRC-1, R-DORM-1)
    - Enabled/disabled state from runtime/database
    - Real thread-safe trigger counts and latest timestamps
    - Summary of evaluations, triggers, errors
    """
    return get_detection_rules_report()


@router.post("/detection-rules/evaluate/{account_id}")
def evaluate_rules_on_account(account_id: str):
    """
    On-demand evaluation of the 6 active detection rules for an account.
    Records evaluation and triggers live in-process telemetry.
    """
    from app.services.rule_engine import evaluate_rules_for_account
    return evaluate_rules_for_account(account_id)


from app.services.dataset_service import get_synthetic_data_report


@router.get("/graph-health")
def read_graph_health(refresh: bool = False):
    """
    Returns real-time graph engine operational and telemetry report:
    - Status: Healthy / Degraded / Unavailable
    - Data source: PostgreSQL
    - Real node count and edge count
    - Connected components, isolated accounts, fan-in/fan-out nodes
    - Cycle participation, multi-hop reachability, network concentration
    - Suspicious connections
    - In-process thread-safe analysis telemetry
    - Sanitized sample topology of highest-risk active fraud cluster (zero PII)
    """
    return get_graph_health_report(force_refresh=refresh)


@router.post("/graph-health/analyze")
def trigger_graph_analysis():
    """
    Triggers an on-demand full graph analysis across PostgreSQL accounts and transactions.
    Updates the in-memory cache and records live analysis telemetry.
    """
    return analyze_graph_topology(force_refresh=True)


@router.get("/synthetic-data")
def read_synthetic_data(refresh: bool = False):
    """
    Returns real PostgreSQL dataset operations and quality monitoring telemetry:
    - Dataset status: Available / Empty / Error
    - Database source: PostgreSQL
    - Real customer, account, and transaction counts
    - Account distribution (Savings vs Current)
    - Ground truth balance (Legitimate Normal vs Suspicious/Mule)
    - Transaction distributions (statuses and types)
    - Full transaction time range (earliest to latest timestamp)
    - Financial aggregates (total and average transaction value in INR)
    - 8 Data quality integrity checks (orphans, duplicates, non-positive amounts, missing fields)
    - ML 26-feature dataset compatibility and non-finite value validation
    - Authoritative generator metadata and data transparency disclosures
    """
    return get_synthetic_data_report(force_refresh=refresh)


@router.post("/synthetic-data/validate")
def trigger_dataset_validation():
    """
    Forces an immediate deep validation scan across all PostgreSQL records,
    re-running all 8 data quality checks and the 26-feature ML compatibility verification.
    """
    return get_synthetic_data_report(force_refresh=True)
from app.services.audit_service import query_internal_audit_logs
from typing import Optional
from fastapi import Query


@router.get("/audit-logs")
def read_internal_audit_logs(
    limit: int = Query(100, ge=1, le=500, description="Page limit (max 500)"),
    offset: int = Query(0, ge=0, description="Page offset"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    category: Optional[str] = Query(None, description="Filter by category (AUTHENTICATION, SECURITY, TRANSACTION, ALERT, CASE, WATCHLIST, DECISION, RULE, ML, GRAPH, SYSTEM)"),
    search: Optional[str] = Query(None, description="Full-text search query across action, actor, entity, details"),
    date_from: Optional[str] = Query(None, description="Earliest ISO timestamp"),
    date_to: Optional[str] = Query(None, description="Latest ISO timestamp"),
):
    """
    Returns unified, sanitized audit events from PostgreSQL application and security logs.
    Includes summary metrics, bounded server-side pagination, and real-time filtering.
    Strictly read-only; does not write audit events on read.
    """
    return query_internal_audit_logs(
        limit=limit,
        offset=offset,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        account_id=account_id,
        category=category,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )

