"""User schemas for API requests and responses."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserPreferences(BaseModel):
    """User fitness and dietary preferences."""

    workout_duration_preference: Optional[int] = Field(None, ge=15, le=180, description="Preferred workout duration in minutes")
    meals_per_day: Optional[int] = Field(None, ge=2, le=8, description="Preferred number of meals per day")
    workout_days_per_week: Optional[int] = Field(None, ge=1, le=7, description="Preferred workout frequency per week")
    preferred_workout_time: Optional[str] = Field(None, description="Preferred workout time (morning, afternoon, evening)")


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: Optional[str] = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password complexity (FR-057)."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least 1 lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least 1 number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least 1 special character")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|non-binary|prefer not to say)$")
    height_cm: Optional[str] = None
    weight_kg: Optional[str] = None
    fitness_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    activity_level: Optional[str] = Field(None, pattern="^(sedentary|lightly active|moderately active|very active)$")
    dietary_restrictions: Optional[list[str]] = None  # ["vegetarian", "vegan", "gluten-free", etc.]
    equipment_access: Optional[list[str]] = None  # ["dumbbells", "barbell", "resistance bands", etc.]
    preferences: Optional[UserPreferences] = None


class UserRead(BaseModel):
    """Schema for user response."""

    id: UUID
    email: str
    name: Optional[str]
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    height_cm: Optional[str]
    weight_kg: Optional[str]
    fitness_level: Optional[str]
    activity_level: Optional[str]
    dietary_restrictions: Optional[list[str]]
    equipment_access: Optional[list[str]]
    preferences: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
