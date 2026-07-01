"""Audit log read API — admin only."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.roles import ADMIN
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    detail: Optional[str]
    created_at: datetime


class PaginatedAuditLogResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    skip: int
    limit: int


@router.get("/", response_model=PaginatedAuditLogResponse)
def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    action: Optional[str] = Query(None, description="Filter by action label"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    """Return paginated audit log entries ordered by created_at DESC. Admin only."""
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)

    total = q.count()
    items = (
        q.order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return PaginatedAuditLogResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )
