"""Pydantic schemas for GroceryShoppingTrip model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroceryShoppingTripBase(BaseModel):
    """Base schema for grocery shopping trips."""

    name: str = Field(..., description="Name of the shopping trip")
    items: dict = Field(..., description="Shopping list items (categorized)")
    estimated_duration_minutes: int | None = Field(None, description="Estimated shopping duration in minutes")
    notes: str | None = Field(None, description="Additional notes for the shopping trip")


class GroceryShoppingTripCreate(GroceryShoppingTripBase):
    """Schema for creating a grocery shopping trip."""
    pass


class GroceryShoppingTripRead(GroceryShoppingTripBase):
    """Schema for reading a grocery shopping trip."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroceryShoppingTripUpdate(BaseModel):
    """Schema for updating a grocery shopping trip."""

    name: str | None = None
    items: dict | None = None
    estimated_duration_minutes: int | None = None
    notes: str | None = None
