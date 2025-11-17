"""
Pydantic schemas for ProgressRecord model.

Supports User Story 2: Follow and Track Schedule
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MeasurementCreate(BaseModel):
    """Schema for creating a measurement record."""

    record_date: date = Field(default_factory=date.today, description="Date of measurement")
    weight_lbs: Decimal | None = Field(None, ge=0, le=1000, description="Weight in pounds")
    body_fat_percentage: Decimal | None = Field(None, ge=0, le=100, description="Body fat percentage")
    measurements: dict[str, float] | None = Field(
        None, description="Additional measurements (chest, waist, arms, etc.)"
    )
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    mood: str | None = Field(None, max_length=50, description="Mood description")
    user_notes: str | None = Field(None, description="User notes about the measurement")

    @field_validator("measurements")
    @classmethod
    def validate_measurements(cls, v: dict[str, float] | None) -> dict[str, float] | None:
        """Validate measurement keys are reasonable."""
        if v is not None:
            allowed_keys = {
                "chest",
                "waist",
                "hips",
                "thighs",
                "arms",
                "calves",
                "neck",
                "shoulders",
            }
            invalid_keys = set(v.keys()) - allowed_keys
            if invalid_keys:
                raise ValueError(f"Invalid measurement keys: {invalid_keys}")
        return v


class MeasurementRead(BaseModel):
    """Schema for reading a measurement record."""

    id: UUID
    user_id: UUID
    fitness_plan_id: UUID | None = None
    record_date: date
    record_type: str
    weight_lbs: Decimal | None = None
    body_fat_percentage: Decimal | None = None
    measurements: dict[str, float] | None = None
    energy_level: int | None = None
    mood: str | None = None
    user_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdherenceStats(BaseModel):
    """Adherence statistics for a time period."""

    total_scheduled: int = Field(..., description="Total activities scheduled")
    total_completed: int = Field(..., description="Total activities completed")
    adherence_rate: Decimal = Field(..., description="Completion rate as percentage")
    workouts_completed: int = Field(..., description="Workouts completed")
    meals_completed: int = Field(..., description="Meals completed")
    current_streak_days: int = Field(0, description="Current consecutive days with activity")
    longest_streak_days: int = Field(0, description="Longest streak achieved")


class MilestoneRead(BaseModel):
    """Schema for reading milestone achievements."""

    id: UUID
    record_date: date
    milestone_description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProgressSummaryRead(BaseModel):
    """Comprehensive progress summary."""

    user_id: UUID
    fitness_plan_id: UUID | None = None
    summary_period: str = Field(..., description="Period covered: 'week', 'month', 'all_time'")

    # Adherence metrics
    adherence: AdherenceStats

    # Recent measurements
    latest_weight_lbs: Decimal | None = None
    weight_change_lbs: Decimal | None = None
    latest_body_fat_percentage: Decimal | None = None

    # Milestones
    recent_milestones: list[MilestoneRead] = Field(default_factory=list)

    # Weekly breakdown
    weekly_stats: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Week-by-week adherence breakdown",
    )


class DailySummaryCreate(BaseModel):
    """Schema for creating a daily progress summary (typically auto-generated)."""

    record_date: date = Field(default_factory=date.today)
    workouts_completed_today: int = Field(0, ge=0)
    meals_completed_today: int = Field(0, ge=0)
    energy_level: int | None = Field(None, ge=1, le=10)
    mood: str | None = Field(None, max_length=50)
    user_notes: str | None = None

