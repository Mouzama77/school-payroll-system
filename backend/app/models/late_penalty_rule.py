import uuid

from sqlalchemy import Float, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LatePenaltyRule(Base):
    """Late penalty rules (DB-driven payroll configuration)."""

    __tablename__ = "late_penalty_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Minimum late days threshold
    late_days_min: Mapped[int] = mapped_column(Integer, nullable=False)

    # Deduction applied when rule matches
    deduction_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional admin label
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)


# ✅ IMPORTANT: enforce fast lookup for payroll engine
Index("ix_late_penalty_rules_late_days_min", LatePenaltyRule.late_days_min)