"""Fitness plan and phase models."""

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
    goal_type = Column(String(500), nullable=False)  # Natural language goal type from user
    goal_description = Column(Text, nullable=False)  # Natural language goal from user
    target_weight_kg = Column(String(10), nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)

    # Plan metadata
    duration_weeks = Column(Integer, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        Enum("draft", "active", "paused", "completed", "abandoned", "replaced", name="plan_status"),
        nullable=False,
        default="draft",
    )

    # Plan versioning - track modifications and evolution
    parent_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="SET NULL"), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)  # Version number within the plan family
    version_notes = Column(Text, nullable=True)  # Description of what changed in this version

    # Plan-level guidance metadata
    key_principles = Column(JSON, nullable=True)  # Core principles guiding the plan (list of strings)
    success_metrics = Column(JSON, nullable=True)  # How to measure success (list of strings)
    important_notes = Column(Text, nullable=True)  # Critical information and warnings

    # Relationships
    user = relationship("User", back_populates="fitness_plans")
    parent_plan = relationship("FitnessPlan", remote_side="FitnessPlan.id", backref="child_plans")
    phases = relationship("Phase", back_populates="fitness_plan", cascade="all, delete-orphan", order_by="Phase.phase_number")
    workout_plans = relationship("WorkoutPlan", back_populates="fitness_plan", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="fitness_plan", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="fitness_plan", cascade="all, delete-orphan")
    schedule = relationship("Schedule", back_populates="fitness_plan", uselist=False, cascade="all, delete-orphan")
    progress_records = relationship("ProgressRecord", back_populates="fitness_plan", cascade="all, delete-orphan")
    disruption_events = relationship("DisruptionEvent", back_populates="fitness_plan", cascade="all, delete-orphan")

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
    grocery_trips = relationship("GroceryShoppingTrip", back_populates="phase", cascade="all, delete-orphan")
    meal_prep_sessions = relationship("MealPrepSession", back_populates="phase", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Phase(id={self.id}, plan_id={self.fitness_plan_id}, phase_number={self.phase_number})>"
