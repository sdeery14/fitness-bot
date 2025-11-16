"""Fitness plan and phase models."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.models import Base, TimestampMixin, UUIDMixin


class FitnessPlan(Base, UUIDMixin, TimestampMixin):
    """Fitness plan model."""

    __tablename__ = "fitness_plans"

    # User association
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Goal definition (FR-001, FR-002, FR-003)
    goal_type = Column(String(100), nullable=False)  # "weight_loss", "muscle_gain", "body_recomposition", "maintenance", etc.
    goal_description = Column(Text, nullable=False)  # Natural language goal from user
    target_weight_kg = Column(String(10), nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)

    # Plan metadata
    duration_weeks = Column(Integer, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        Enum("draft", "active", "paused", "completed", "abandoned", name="plan_status"),
        nullable=False,
        default="draft",
    )

    # AI-generated plan snapshot (FR-009, FR-010)
    plan_snapshot = Column(JSON, nullable=False)  # Complete plan structure for reference

    # Relationships
    user = relationship("User", back_populates="fitness_plans")
    phases = relationship("Phase", back_populates="fitness_plan", cascade="all, delete-orphan", order_by="Phase.phase_number")
    workout_plans = relationship("WorkoutPlan", back_populates="fitness_plan", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="fitness_plan", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="fitness_plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FitnessPlan(id={self.id}, user_id={self.user_id}, goal={self.goal_type})>"


class Phase(Base, UUIDMixin, TimestampMixin):
    """Fitness plan phase model (FR-012, FR-013)."""

    __tablename__ = "phases"

    # Plan association
    fitness_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Phase metadata
    phase_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    name = Column(String(255), nullable=False)  # "Foundation Phase", "Strength Building Phase", etc.
    objectives = Column(JSON, nullable=False)  # ["Build base strength", "Learn proper form", etc.]

    # Phase dates
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Phase-specific details (FR-014)
    phase_details = Column(JSON, nullable=False)  # Intensity, volume, focus areas, etc.

    # Relationships
    fitness_plan = relationship("FitnessPlan", back_populates="phases")
    workouts = relationship("Workout", back_populates="phase", cascade="all, delete-orphan")
    meals = relationship("Meal", back_populates="phase", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Phase(id={self.id}, plan_id={self.fitness_plan_id}, phase_number={self.phase_number})>"
