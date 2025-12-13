"""Meal prep session model."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Text, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.models.schedule import ScheduleEntry


class MealPrepSession(Base):
    """Meal prep session with recipes and instructions."""

    __tablename__ = "meal_prep_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Recipes as JSON array of strings
    # Example: ["Grilled Chicken Breast", "Brown Rice", "Roasted Vegetables"]
    recipes: Mapped[list] = mapped_column(JSON, nullable=False)
    
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Cooking instructions as JSON array of strings
    # Example: ["1. Preheat oven to 400°F", "2. Season chicken..."]
    instructions: Mapped[list] = mapped_column(JSON, nullable=False)
    
    storage_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(
        "ScheduleEntry",
        back_populates="meal_prep_session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<MealPrepSession(id={self.id}, session_name='{self.session_name}')>"
