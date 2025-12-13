"""Pydantic schemas for MealPrepSession model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MealPrepSessionBase(BaseModel):
    """Base schema for meal prep sessions."""

    session_name: str = Field(..., description="Name of the prep session")
    recipes: list = Field(..., description="List of recipes to prepare")
    duration_minutes: int = Field(..., description="Duration of the prep session in minutes")
    batch_size: int = Field(..., description="Number of servings/meals to prepare")
    instructions: list = Field(..., description="Step-by-step cooking instructions")
    storage_instructions: str | None = Field(None, description="How to store the prepared food")
    notes: str | None = Field(None, description="Additional notes for the prep session")


class MealPrepSessionCreate(MealPrepSessionBase):
    """Schema for creating a meal prep session."""
    pass


class MealPrepSessionRead(MealPrepSessionBase):
    """Schema for reading a meal prep session."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealPrepSessionUpdate(BaseModel):
    """Schema for updating a meal prep session."""

    session_name: str | None = None
    recipes: list | None = None
    duration_minutes: int | None = None
    batch_size: int | None = None
    instructions: list | None = None
    storage_instructions: str | None = None
    notes: str | None = None
