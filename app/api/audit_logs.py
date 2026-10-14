from typing import Optional
from fastapi import APIRouter, Depends, Query, Response

from app.api.auth import require_role
from app.services.audit_service import (
    query_internal_audit_logs,
    get_audit_summary,
)


router = APIRouter(
    prefix="/api/v1/audit-logs",
    tags=["Audit Logs"],
    dependencies=[Depends(require_role(["internal_team", "bank_compliance"]))],
)


@router.get(
    "/summary",
    summary="Get audit summary counters directly from PostgreSQL",
)
def read_audit_summary():
    """
    Returns unified summary counts across application and security audit trails.
    Computed directly from PostgreSQL audit_logs and auth_audit_log tables.
    """
    return get_audit_summary()


@router.get(
    "",
    summary="Query unified, sanitized audit logs from PostgreSQL",
)
def get_audit_logs(
    response: Response,
    limit: int = Query(default=100, ge=1, le=500, description="Max audit logs to return (1-500)"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    category: Optional[str] = Query(default=None, description="Filter by category (AUTHENTICATION, SECURITY, TRANSACTION, ALERT, CASE, WATCHLIST, DECISION, RULE, ML, GRAPH, SYSTEM)"),
    action: Optional[str] = Query(default=None, description="Filter by action name"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(default=None, description="Filter by entity ID"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
    search: Optional[str] = Query(default=None, description="Full text search query"),
    date_from: Optional[str] = Query(default=None, description="Earliest ISO timestamp"),
    date_to: Optional[str] = Query(default=None, description="Latest ISO timestamp"),
    format: Optional[str] = Query(default="list", description="Response format: 'list' (default) or 'envelope'"),
):
    """
    Queries unified PostgreSQL audit logs across application and security tables.
    All sensitive secrets (passwords, tokens, vectors, hashes) are strictly redacted.
    Returns list of items by default (or envelope with pagination & summary if format='envelope').
    """
    result = query_internal_audit_logs(
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
    response.headers["X-Total-Count"] = str(result["pagination"]["total"])
    if format == "envelope":
        return result
    return result["items"]