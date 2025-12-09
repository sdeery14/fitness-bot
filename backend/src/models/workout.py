"""Workout and exercise models."""

from sqlalchemy import Column, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from src.models import Base, TimestampMixin, UUIDMixin


class WorkoutPlan(Base, UUIDMixin, TimestampMixin):
    """Workout plan model (FR-015)."""

    __tablename__ = "workout_plans"

    # Plan association
    fitness_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Workout plan configuration
    frequency_per_week = Column(Integer, nullable=False)  # 3, 4, 5, etc. (FR-016)
    progression_strategy = Column(String(255), nullable=False)  # "linear", "wave", "double progression", etc.

    # Workout plan details (FR-017, FR-018)
    workout_plan_details = Column(JSON, nullable=False)  # Split type, focus areas, rest days, etc.

    # Relationships
    fitness_plan = relationship("FitnessPlan", back_populates="workout_plans")
    workouts = relationship("Workout", back_populates="workout_plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<WorkoutPlan(id={self.id}, plan_id={self.fitness_plan_id}, frequency={self.frequency_per_week})>"


class Workout(Base, UUIDMixin, TimestampMixin):
    """Individual workout model (FR-019, FR-020)."""

    __tablename__ = "workouts"

    # Plan association
    workout_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    phase_id = Column(PGUUID(as_uuid=True), ForeignKey("phases.id", ondelete="CASCADE"), nullable=False, index=True)

    # Workout metadata
    name = Column(String(255), nullable=False)  # "Upper Body Push Day", "Leg Day", etc.
    workout_type = Column(String(100), nullable=False)  # "strength", "cardio", "flexibility", "hybrid"
    duration_minutes = Column(Integer, nullable=False)
    intensity_level = Column(String(50), nullable=False)  # "low", "moderate", "high"

    # Workout structure (FR-021)
    workout_structure = Column(JSON, nullable=False)  # Warm-up, main sets, cool-down, rest periods, etc.

    # Relationships
    workout_plan = relationship("WorkoutPlan", back_populates="workouts")
    phase = relationship("Phase", back_populates="workouts")
    exercises = relationship("Exercise", back_populates="workout", cascade="all, delete-orphan", order_by="Exercise.exercise_order")

    def __repr__(self) -> str:
        return f"<Workout(id={self.id}, name={self.name}, type={self.workout_type})>"


class Exercise(Base, UUIDMixin, TimestampMixin):
    """Exercise model (FR-022, FR-048, FR-049, FR-050)."""

    __tablename__ = "exercises"

    # Workout association
    workout_id = Column(PGUUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Exercise ordering
    exercise_order = Column(Integer, nullable=False)

    # Exercise details from curated database (FR-048, FR-049)
    name = Column(String(255), nullable=False)
    exercise_type = Column(String(100), nullable=False)  # "compound", "isolation", "cardio", "plyometric", etc.
    target_muscle_groups = Column(JSON, nullable=False)  # ["chest", "shoulders", "triceps"]
    equipment_required = Column(JSON, nullable=False)  # ["barbell", "bench"] or ["bodyweight"]

    # Exercise prescription (FR-022, FR-023)
    sets = Column(Integer, nullable=True)  # Null for cardio/time-based exercises
    reps = Column(String(50), nullable=True)  # "8-12", "15", "AMRAP", null for time-based
    duration_seconds = Column(Integer, nullable=True)  # For cardio/timed exercises
    rest_seconds = Column(Integer, nullable=False)  # Rest between sets
    tempo = Column(String(50), nullable=True)  # "3-1-3-1" (eccentric-pause-concentric-pause)
    rpe_target = Column(Integer, nullable=True)  # Rate of Perceived Exertion 1-10

    # Exercise instructions and alternatives (FR-050, FR-051)
    instructions = Column(Text, nullable=False)  # Step-by-step execution
    form_cues = Column(JSON, nullable=True)  # ["Keep core tight", "Full range of motion"]
    alternative_exercise_ids = Column(JSON, nullable=True)  # UUIDs of alternative exercises

    # Vector embedding for semantic search (384 dimensions for sentence-transformers/all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=True)  # Semantic search embedding

    # Relationships
    workout = relationship("Workout", back_populates="exercises")

    def __repr__(self) -> str:
        return f"<Exercise(id={self.id}, name={self.name}, workout_id={self.workout_id})>"
