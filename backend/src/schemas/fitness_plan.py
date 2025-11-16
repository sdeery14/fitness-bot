"""Fitness plan schemas for API requests and responses."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PhaseRead(BaseModel):
    """Schema for fitness plan phase response."""

    id: UUID
    phase_number: int = Field(..., ge=1, description="Phase number (1, 2, 3, etc.)")
    name: str
    objectives: list[str] = Field(..., description="Phase objectives")
    start_date: datetime
    end_date: datetime
    phase_details: dict = Field(..., description="Phase-specific configuration (intensity, volume, focus)")
    created_at: datetime

    class Config:
        from_attributes = True


class FitnessPlanCreate(BaseModel):
    """Schema for creating a fitness plan."""

    goal_type: str = Field(..., description="Goal type: weight_loss, muscle_gain, body_recomposition, maintenance")
    goal_description: str = Field(..., min_length=10, description="Natural language goal description from user")
    target_weight_kg: Optional[str] = None
    target_date: Optional[datetime] = None
    duration_weeks: int = Field(..., ge=1, le=52, description="Plan duration in weeks")


class FitnessPlanUpdate(BaseModel):
    """Schema for updating a fitness plan."""

    status: Optional[str] = Field(None, pattern="^(draft|active|completed|abandoned)$")
    target_weight_kg: Optional[str] = None
    target_date: Optional[datetime] = None


class FitnessPlanRead(BaseModel):
    """Schema for fitness plan response."""

    id: UUID
    user_id: UUID
    goal_type: str
    goal_description: str
    target_weight_kg: Optional[str]
    target_date: Optional[datetime]
    duration_weeks: int
    start_date: datetime
    end_date: datetime
    status: str
    plan_snapshot: dict = Field(..., description="Complete AI-generated plan structure")
    phases: list[PhaseRead] = Field(default_factory=list, description="Plan phases")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
