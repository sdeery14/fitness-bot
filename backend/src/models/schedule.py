"""
Schedule and ScheduleEntry models for daily workout and meal scheduling.

These models support User Story 2: Follow and Track Schedule
"""

from datetime import date, datetime, time
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin

if TYPE_CHECKING:
    from .fitness_plan import FitnessPlan
    from .meal import Meal
    from .user import User
    from .workout import Workout


class Schedule(Base, TimestampMixin):
    """
    Represents the user's day-to-day timeline of workouts and meals.

    Each fitness plan has exactly one schedule that maps the plan's
    workouts and meals to specific dates and times.
    """

    __tablename__ = "schedules"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    fitness_plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="CASCADE"), nullable=False
    )

    # Schedule metadata
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_recalculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    recalculation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="schedules")
    fitness_plan: Mapped["FitnessPlan"] = relationship("FitnessPlan", back_populates="schedule")
    entries: Mapped[list["ScheduleEntry"]] = relationship(
        "ScheduleEntry",
        back_populates="schedule",
        cascade="all, delete-orphan",
        order_by="ScheduleEntry.entry_date, ScheduleEntry.entry_time",
    )

    __table_args__ = (
        UniqueConstraint("fitness_plan_id", name="one_schedule_per_plan"),
        Index("idx_schedules_user", "user_id"),
        Index("idx_schedules_fitness_plan", "fitness_plan_id"),
    )

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, user_id={self.user_id}, start_date={self.start_date})>"


class ScheduleEntry(Base, TimestampMixin):
    """
    Represents a specific workout or meal scheduled for a particular date/time.

    Tracks completion status and allows users to mark activities as complete,
    skip them, or reschedule them.
    """

    __tablename__ = "schedule_entries"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    schedule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False
    )

    # Entry type and scheduling
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'workout' or 'meal'
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    entry_time: Mapped[time | None] = mapped_column(
        Time, nullable=True
    )  # Optional, for meal timing

    # Reference to actual workout or meal
    workout_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True
    )
    meal_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("meals.id", ondelete="SET NULL"), nullable=True
    )

    # Grocery shopping data (for entry_type='grocery_shopping')
    # Structure: {"items": [{"ingredient": "Chicken breast", "quantity": "2 lbs", "category": "Meat", "fdc_id": 12345}, ...]}
    grocery_list: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Meal prep instructions (for entry_type='meal_prep')
    # Structure: {\"recipes\": [{\"meal_name\": \"Grilled Chicken\", \"batch_size\": 4, \"steps\": [...], \"storage\": \"...\"}], \"duration_minutes\": 90}
    prep_instructions: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Completion tracking
    completion_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'scheduled'")
    )  # scheduled, completed, skipped, rescheduled
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # User notes
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    skipped_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="entries")
    workout: Mapped["Workout | None"] = relationship("Workout", foreign_keys=[workout_id])
    meal: Mapped["Meal | None"] = relationship("Meal", foreign_keys=[meal_id])

    __table_args__ = (
        CheckConstraint(
            "(entry_type = 'workout' AND workout_id IS NOT NULL AND meal_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NULL) OR "
            "(entry_type = 'meal' AND meal_id IS NOT NULL AND workout_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NULL) OR "
            "(entry_type = 'grocery_shopping' AND workout_id IS NULL AND meal_id IS NULL AND grocery_list IS NOT NULL AND prep_instructions IS NULL) OR "
            "(entry_type = 'meal_prep' AND workout_id IS NULL AND meal_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NOT NULL)",
            name="valid_entry_reference",
        ),
        Index("idx_schedule_entries_schedule", "schedule_id"),
        Index("idx_schedule_entries_date", "entry_date"),
        Index("idx_schedule_entries_user_date", "schedule_id", "entry_date"),
        Index("idx_schedule_entries_status", "completion_status"),
        Index("idx_schedule_entries_workout", "workout_id"),
        Index("idx_schedule_entries_meal", "meal_id"),
    )

    def __repr__(self) -> str:
        return f"<ScheduleEntry(id={self.id}, type={self.entry_type}, date={self.entry_date}, status={self.completion_status})>"
