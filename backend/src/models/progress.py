"""
ProgressRecord model for tracking user progress, adherence, and milestones.

Supports User Story 2: Follow and Track Schedule
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin

if TYPE_CHECKING:
    from .fitness_plan import FitnessPlan
    from .user import User


class ProgressRecord(Base, TimestampMixin):
    """
    Represents historical tracking data and milestones.

    Tracks daily completion stats, measurements, adherence metrics,
    and milestone achievements.
    """

    __tablename__ = "progress_records"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fitness_plan_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="SET NULL"), nullable=True)

    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)  # daily_summary, milestone, measurement

    # Completion stats
    workouts_completed_today: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    meals_completed_today: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    # Measurements (optional, depends on record_type)
    weight_lbs: Mapped[Decimal | None] = mapped_column(nullable=True)
    body_fat_percentage: Mapped[Decimal | None] = mapped_column(nullable=True)
    measurements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {"chest": 40, "waist": 32, "arms": 14}

    # Calculated metrics
    weekly_adherence_rate: Mapped[Decimal | None] = mapped_column(nullable=True)  # Percentage
    total_workouts_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_streak_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Milestones
    milestone_achieved: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    milestone_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User input
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    mood: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="progress_records")
    fitness_plan: Mapped["FitnessPlan | None"] = relationship("FitnessPlan", back_populates="progress_records")

    __table_args__ = (
        CheckConstraint("energy_level IS NULL OR (energy_level BETWEEN 1 AND 10)", name="valid_energy_level"),
        Index("idx_progress_records_user", "user_id"),
        Index("idx_progress_records_date", "record_date"),
        Index("idx_progress_records_user_date", "user_id", "record_date", postgresql_using="btree"),
        Index("idx_progress_records_type", "record_type"),
        Index("idx_progress_records_milestones", "milestone_achieved", postgresql_where="milestone_achieved = true"),
    )

    def __repr__(self) -> str:
        return f"<ProgressRecord(id={self.id}, user_id={self.user_id}, date={self.record_date}, type={self.record_type})>"
