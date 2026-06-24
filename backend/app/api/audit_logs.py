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
    created_at: datetime  # serialised as ISO string


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    search: Optional[str] = Query(None, description="Free-text search in detail field"),
    action: Optional[str] = Query(None, description="Filter by action label"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    date_from: Optional[date] = Query(None, description="Inclusive start date"),
    date_to: Optional[date] = Query(None, description="Inclusive end date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    """Return paginated audit log entries. Admin only."""
    q = db.query(AuditLog)
    if search:
        q = q.filter(AuditLog.detail.ilike(f"%{search}%"))
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)

    offset = (page - 1) * page_size
    return (
        q.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
