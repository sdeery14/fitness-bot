"""
Pydantic schemas for Schedule and ScheduleEntry models.

Supports User Story 2: Follow and Track Schedule
"""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScheduleEntryBase(BaseModel):
    """Base schema for schedule entries."""

    entry_type: str = Field(..., description="Type of entry: 'workout', 'meal', 'grocery_shopping', or 'meal_prep'")
    entry_date: date = Field(..., description="Date scheduled for this entry")
    entry_time: time | None = Field(None, description="Optional time for meal entries")


class ScheduleEntryCreate(ScheduleEntryBase):
    """Schema for creating a schedule entry."""

    workout_id: UUID | None = None
    meal_id: UUID | None = None
    grocery_list: dict | None = Field(None, description="Shopping list for grocery_shopping entries")
    prep_instructions: dict | None = Field(None, description="Cooking instructions for meal_prep entries")


class ScheduleEntryRead(ScheduleEntryBase):
    """Schema for reading a schedule entry."""

    id: UUID
    schedule_id: UUID
    workout_id: UUID | None = None
    meal_id: UUID | None = None
    grocery_list: dict | None = Field(None, description="Shopping list for grocery_shopping entries")
    prep_instructions: dict | None = Field(None, description="Cooking instructions for meal_prep entries")
    completion_status: str = Field(..., description="Status: scheduled, completed, skipped, rescheduled")
    completed_at: datetime | None = None
    user_notes: str | None = None
    skipped_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    # Optional related data (populated via joins)
    workout_name: str | None = None
    meal_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleEntryComplete(BaseModel):
    """Schema for marking a schedule entry as complete."""

    user_notes: str | None = Field(None, description="Optional user notes about completion")


class ScheduleEntrySkip(BaseModel):
    """Schema for skipping a schedule entry."""

    skipped_reason: str | None = Field(None, description="Optional reason for skipping")



class ScheduleRead(BaseModel):
    """Schema for reading a schedule."""

    id: UUID
    user_id: UUID
    fitness_plan_id: UUID
    start_date: date
    last_recalculated_at: datetime
    recalculation_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TodayScheduleResponse(BaseModel):
    """Response schema for today's schedule."""

    date: date
    entries: list[ScheduleEntryRead]
    summary: dict[str, int] = Field(
        default_factory=dict,
        description="Summary stats: total_workouts, total_meals, completed_count, etc.",
    )


class UpcomingScheduleResponse(BaseModel):
    """Response schema for upcoming schedule (next 14 days)."""

    start_date: date
    end_date: date
    entries: list[ScheduleEntryRead]
    grouped_by_date: dict[str, list[ScheduleEntryRead]] = Field(
        default_factory=dict, description="Entries grouped by date for calendar view"
    )

