"""Workout schemas for API requests and responses."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExerciseRead(BaseModel):
    """Schema for exercise response."""

    id: UUID
    exercise_order: int
    name: str
    exercise_type: str = Field(..., description="Type: compound, isolation, cardio, plyometric")
    target_muscle_groups: list[str] = Field(..., description="Target muscles")
    equipment_required: list[str] = Field(..., description="Required equipment")
    sets: Optional[int] = Field(None, ge=1, description="Number of sets (null for time-based)")
    reps: Optional[str] = Field(None, description="Rep range (e.g., '8-12', '15', 'AMRAP')")
    duration_seconds: Optional[int] = Field(None, ge=1, description="Duration for cardio/timed exercises")
    rest_seconds: int = Field(..., ge=0, description="Rest between sets in seconds")
    tempo: Optional[str] = Field(None, description="Tempo notation (e.g., '3-1-3-1')")
    rpe_target: Optional[int] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion (1-10)")
    instructions: str = Field(..., description="Step-by-step execution instructions")
    form_cues: Optional[list[str]] = Field(None, description="Form cues for proper technique")
    alternative_exercise_ids: Optional[list[UUID]] = Field(None, description="Alternative exercise UUIDs")

    class Config:
        from_attributes = True


class WorkoutRead(BaseModel):
    """Schema for workout response."""

    id: UUID
    workout_plan_id: UUID
    phase_id: UUID
    name: str
    workout_type: str = Field(..., description="Type: strength, cardio, flexibility, hybrid")
    duration_minutes: int = Field(..., ge=1, description="Estimated duration in minutes")
    intensity_level: str = Field(..., description="Intensity: low, moderate, high")
    workout_structure: dict = Field(..., description="Structure: warm-up, main sets, cool-down, rest periods")
    exercises: list[ExerciseRead] = Field(default_factory=list, description="Exercises in workout order")
    created_at: str

    class Config:
        from_attributes = True


class WorkoutPlanRead(BaseModel):
    """Schema for workout plan response."""

    id: UUID
    fitness_plan_id: UUID
    frequency_per_week: int = Field(..., ge=1, le=7, description="Workouts per week")
    progression_strategy: str = Field(..., description="Progression strategy: linear, wave, double progression")
    workout_plan_details: dict = Field(..., description="Split type, focus areas, rest days")
    workouts: list[WorkoutRead] = Field(default_factory=list, description="All workouts in plan")

    class Config:
        from_attributes = True
