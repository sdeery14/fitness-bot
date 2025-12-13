"""Grocery shopping trip model."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Text, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.models.schedule import ScheduleEntry


class GroceryShoppingTrip(Base):
    """Grocery shopping trip with categorized shopping list."""

    __tablename__ = "grocery_shopping_trips"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Shopping list as JSON array of categorized items
    # Structure: [{"category": "Produce", "items": [{"name": "Bananas", "quantity": "6", "notes": "ripe"}]}]
    items: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(
        "ScheduleEntry",
        back_populates="grocery_trip",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<GroceryShoppingTrip(id={self.id}, name='{self.name}')>"
