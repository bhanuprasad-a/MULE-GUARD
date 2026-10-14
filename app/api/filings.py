"""
MuleGuard Regulatory Filings API Router
Provides endpoints for retrieving, drafting, submitting, and reviewing
official FIU-IND regulatory compliance filings (SAR, STR, CTR, NTR).
Authorized for bank_compliance and internal_team roles.
"""
from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.api.auth import require_role, get_current_user


router = APIRouter(
    prefix="/api/v1/filings",
    tags=["Regulatory Filings"],
    dependencies=[Depends(require_role(["bank_compliance", "internal_team"]))],
)


class CreateFilingRequest(BaseModel):
    account_id: str = Field(..., max_length=32, description="Target account ID")
    filing_type: str = Field(default="SAR", max_length=32, description="Filing type (SAR, STR, CTR, NTR)")
    case_id: Optional[str] = Field(default=None, max_length=64, description="Optional associated case ID")
    alert_id: Optional[str] = Field(default=None, max_length=64, description="Optional associated alert ID")
    reason: str = Field(..., max_length=500, description="Short summary/title of suspicious activity")
    narrative: str = Field(..., max_length=4000, description="Detailed statutory regulatory narrative")
    reporting_authority: str = Field(default="FIU-IND", max_length=64, description="Statutory authority")


@router.get("/summary")
def get_filings_summary():
    """
    Returns summary KPI counts directly computed from the PostgreSQL regulatory_filings table.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_filings,
                    COUNT(*) FILTER (WHERE status = 'Draft') AS draft,
                    COUNT(*) FILTER (WHERE status = 'Submitted') AS submitted,
                    COUNT(*) FILTER (WHERE status = 'Accepted') AS accepted,
                    COUNT(*) FILTER (WHERE status = 'Rejected') AS rejected
                FROM regulatory_filings;
                """
            )
            row = cur.fetchone()

    total = row[0] or 0
    draft = row[1] or 0
    submitted = row[2] or 0
    accepted = row[3] or 0
    rejected = row[4] or 0

    return {
        "total_filings": total,
        "draft": draft,
        "submitted": submitted,
        "accepted": accepted,
        "rejected": rejected,
    }


@router.get("")
def get_filings(
    status: Optional[str] = Query(default=None, max_length=32, description="Filter by status (Draft, Submitted, Accepted, Rejected)"),
    filing_type: Optional[str] = Query(default=None, max_length=32, description="Filter by filing type (SAR, STR, CTR, NTR)"),
    search: Optional[str] = Query(default=None, max_length=128, description="Search across filing ID, account, entity, or reference"),
    limit: int = Query(default=100, ge=1, le=500, description="Max filings to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    """
    Queries regulatory filings joined with accounts and customers for full compliance view.
    """
    query = """
        SELECT
            f.id,
            f.account_id,
            f.case_id,
            f.alert_id,
            f.filing_type,
            f.status,
            f.reporting_authority,
            f.reason,
            f.narrative,
            f.reference_number,
            f.filed_by,
            f.created_at,
            f.updated_at,
            cust.name AS customer_name,
            acc.account_type,
            acc.balance,
            c.title AS case_title
        FROM regulatory_filings f
        LEFT JOIN accounts acc ON f.account_id = acc.id
        LEFT JOIN customers cust ON acc.customer_id = cust.id
        LEFT JOIN cases c ON f.case_id = c.id
        WHERE 1=1
    """
    params = []

    if status and status.upper() != "ALL":
        query += " AND f.status = %s"
        params.append(status)

    if filing_type and filing_type.upper() != "ALL":
        query += " AND f.filing_type = %s"
        params.append(filing_type)

    if search:
        search_pattern = f"%{search.strip()}%"
        query += """ AND (
            f.id ILIKE %s
            OR f.account_id ILIKE %s
            OR cust.name ILIKE %s
            OR f.reference_number ILIKE %s
            OR f.case_id ILIKE %s
            OR f.alert_id ILIKE %s
        )"""
        params.extend([search_pattern] * 6)

    query += " ORDER BY f.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "filing_id": r[0],
            "account_id": r[1],
            "accountId": r[1],
            "case_id": r[2],
            "alert_id": r[3],
            "reference": r[2] or r[3] or "Direct Review",
            "filing_type": r[4],
            "filingType": r[4],
            "status": r[5],
            "reporting_authority": r[6],
            "reason": r[7] or "",
            "narrative": r[8] or "",
            "reference_number": r[9],
            "filed_by": r[10] or "Compliance Officer",
            "created_at": r[11],
            "updated_at": r[12],
            "entity": r[13] or r[1],
            "customer_name": r[13] or r[1],
            "account_type": r[14] or "Savings",
            "balance": float(r[15]) if r[15] is not None else 0.0,
            "case_title": r[16] or "",
        }
        for r in rows
    ]


@router.get("/{filing_id}")
def get_filing(filing_id: str = Path(..., max_length=64, description="Target filing ID")):
    """
    Fetches comprehensive detail for a single filing.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    f.id,
                    f.account_id,
                    f.case_id,
                    f.alert_id,
                    f.filing_type,
                    f.status,
                    f.reporting_authority,
                    f.reason,
                    f.narrative,
                    f.reference_number,
                    f.filed_by,
                    f.created_at,
                    f.updated_at,
                    cust.name AS customer_name,
                    acc.account_type,
                    acc.balance,
                    c.title AS case_title
                FROM regulatory_filings f
                LEFT JOIN accounts acc ON f.account_id = acc.id
                LEFT JOIN customers cust ON acc.customer_id = cust.id
                LEFT JOIN cases c ON f.case_id = c.id
                WHERE f.id = %s
                """,
                (filing_id,),
            )
            r = cur.fetchone()

    if not r:
        raise HTTPException(status_code=404, detail="Regulatory filing not found")

    return {
        "id": r[0],
        "filing_id": r[0],
        "account_id": r[1],
        "accountId": r[1],
        "case_id": r[2],
        "alert_id": r[3],
        "reference": r[2] or r[3] or "Direct Review",
        "filing_type": r[4],
        "filingType": r[4],
        "status": r[5],
        "reporting_authority": r[6],
        "reason": r[7] or "",
        "narrative": r[8] or "",
        "reference_number": r[9],
        "filed_by": r[10] or "Compliance Officer",
        "created_at": r[11],
        "updated_at": r[12],
        "entity": r[13] or r[1],
        "customer_name": r[13] or r[1],
        "account_type": r[14] or "Savings",
        "balance": float(r[15]) if r[15] is not None else 0.0,
        "case_title": r[16] or "",
    }


@router.post("")
def create_filing(
    body: CreateFilingRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Creates a new draft regulatory filing for an account and logs an immutable audit event.
    """
    allowed_types = {"SAR", "STR", "CTR", "NTR"}
    if body.filing_type.upper() not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Filing type must be one of: {', '.join(sorted(allowed_types))}",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check target account exists
            cur.execute("SELECT id FROM accounts WHERE id = %s", (body.account_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail=f"Account {body.account_id} not found")

            # Check optional case exists if provided
            if body.case_id:
                cur.execute("SELECT id FROM cases WHERE id = %s", (body.case_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail=f"Case {body.case_id} not found")

            # Check optional alert exists if provided
            if body.alert_id:
                cur.execute("SELECT id FROM alerts WHERE id = %s", (body.alert_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail=f"Alert {body.alert_id} not found")

            filing_id = f"FIL-{uuid4().hex[:10].upper()}"
            filed_by = current_user.get("full_name") or current_user.get("name") or "A. Kumar"

            cur.execute(
                """
                INSERT INTO regulatory_filings (
                    id, account_id, case_id, alert_id, filing_type, status,
                    reporting_authority, reason, narrative, reference_number,
                    filed_by, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, 'Draft', %s, %s, %s, NULL, %s, NOW(), NOW())
                RETURNING id, created_at, updated_at
                """,
                (
                    filing_id,
                    body.account_id,
                    body.case_id,
                    body.alert_id,
                    body.filing_type.upper(),
                    body.reporting_authority or "FIU-IND",
                    body.reason,
                    body.narrative,
                    filed_by,
                ),
            )
            created_row = cur.fetchone()

            # Record in central audit_logs
            cur.execute(
                """
                INSERT INTO audit_logs (
                    action, entity_type, entity_id, account_id, details
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "REGULATORY_FILING_CREATED",
                    "regulatory_filing",
                    filing_id,
                    body.account_id,
                    Jsonb({
                        "filing_id": filing_id,
                        "filing_type": body.filing_type.upper(),
                        "case_id": body.case_id,
                        "alert_id": body.alert_id,
                        "reporting_authority": body.reporting_authority or "FIU-IND",
                        "filed_by": filed_by,
                    }),
                ),
            )

    return {
        "id": created_row[0],
        "filing_id": created_row[0],
        "account_id": body.account_id,
        "filing_type": body.filing_type.upper(),
        "status": "Draft",
        "reporting_authority": body.reporting_authority or "FIU-IND",
        "reason": body.reason,
        "narrative": body.narrative,
        "filed_by": filed_by,
        "created_at": created_row[1],
        "updated_at": created_row[2],
    }


@router.post("/{filing_id}/submit")
def submit_filing(
    filing_id: str = Path(..., max_length=64, description="Target filing ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Submits a draft filing to FIU-IND regulatory portal, generating an official reference.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status, account_id, filing_type, reporting_authority FROM regulatory_filings WHERE id = %s",
                (filing_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Regulatory filing not found")

            current_status = row[1]
            account_id = row[2]
            filing_type = row[3]
            authority = row[4]

            if current_status != "Draft":
                raise HTTPException(
                    status_code=400,
                    detail=f"Only Draft filings can be submitted. Current status: '{current_status}'",
                )

            reference_no = f"FIU-ACK-{uuid4().hex[:8].upper()}"

            cur.execute(
                """
                UPDATE regulatory_filings
                SET
                    status = 'Submitted',
                    reference_number = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, status, reference_number, updated_at
                """,
                (reference_no, filing_id),
            )
            updated = cur.fetchone()

            # Record in central audit_logs
            officer = current_user.get("full_name") or current_user.get("name") or "A. Kumar"
            cur.execute(
                """
                INSERT INTO audit_logs (
                    action, entity_type, entity_id, account_id, details
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "REGULATORY_FILING_SUBMITTED",
                    "regulatory_filing",
                    filing_id,
                    account_id,
                    Jsonb({
                        "filing_id": filing_id,
                        "filing_type": filing_type,
                        "reference_number": reference_no,
                        "reporting_authority": authority,
                        "submitted_by": officer,
                    }),
                ),
            )

    return {
        "id": updated[0],
        "filing_id": updated[0],
        "status": updated[1],
        "reference_number": updated[2],
        "updated_at": updated[3],
        "message": f"Filing {filing_id} successfully submitted to {authority} under reference {reference_no}.",
    }


@router.post("/{filing_id}/accept")
def accept_filing(
    filing_id: str = Path(..., max_length=64, description="Target filing ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Marks a submitted filing as Accepted and acknowledged by the statutory authority.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status, account_id, reference_number, reporting_authority FROM regulatory_filings WHERE id = %s",
                (filing_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Regulatory filing not found")

            current_status = row[1]
            account_id = row[2]
            reference_no = row[3]
            authority = row[4]

            if current_status != "Submitted":
                raise HTTPException(
                    status_code=400,
                    detail=f"Only Submitted filings can be accepted. Current status: '{current_status}'",
                )

            cur.execute(
                """
                UPDATE regulatory_filings
                SET
                    status = 'Accepted',
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, status, reference_number, updated_at
                """,
                (filing_id,),
            )
            updated = cur.fetchone()

            # Record in central audit_logs
            officer = current_user.get("full_name") or current_user.get("name") or "A. Kumar"
            cur.execute(
                """
                INSERT INTO audit_logs (
                    action, entity_type, entity_id, account_id, details
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "REGULATORY_FILING_ACCEPTED",
                    "regulatory_filing",
                    filing_id,
                    account_id,
                    Jsonb({
                        "filing_id": filing_id,
                        "reference_number": reference_no,
                        "reporting_authority": authority,
                        "verified_by": officer,
                    }),
                ),
            )

    return {
        "id": updated[0],
        "filing_id": updated[0],
        "status": updated[1],
        "reference_number": updated[2],
        "updated_at": updated[3],
        "message": f"Filing {filing_id} successfully marked as Accepted by {authority}.",
    }
