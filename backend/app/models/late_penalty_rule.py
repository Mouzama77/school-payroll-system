import uuid

from sqlalchemy import Float, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LatePenaltyRule(Base):
    """Late penalty rules — Phase 2 DB-driven payroll configuration.

    Each row defines a lateness tier: when an employee's late_minutes falls
    in [min_late_minutes, max_late_minutes] the corresponding deduction_type
    is applied during payroll generation.
    """

    __tablename__ = "late_penalty_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Lower bound of late minutes for this tier (inclusive)
    min_late_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Upper bound of late minutes for this tier (NULL = no upper bound)
    max_late_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Deduction type: "none" | "warning" | "half_day" | "full_day"
    deduction_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Human-readable label for the admin UI
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)


Index("ix_late_penalty_rules_min_late_minutes", LatePenaltyRule.min_late_minutes)