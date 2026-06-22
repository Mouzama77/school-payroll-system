"""Audit log model.

Records every significant mutation: leave approvals/rejections and
attendance overrides. All writes happen inside the same transaction as the
mutation they describe, so the audit trail is always consistent with the data.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # The user who performed the action.
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Short machine-readable label, e.g. "LEAVE_APPROVED", "ATTENDANCE_OVERRIDDEN".
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Which table the affected row belongs to, e.g. "leave", "attendance".
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # The UUID of the affected row.
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Human-readable description of the change.
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
