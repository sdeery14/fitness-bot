"""Grocery shopping trip model."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.models.fitness_plan import Phase
    from src.models.schedule import ScheduleEntry


class GroceryShoppingTrip(Base):
    """Grocery shopping trip with categorized shopping list."""

    __tablename__ = "grocery_shopping_trips"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Phase association
    phase_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("phases.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Shopping list as JSON array of categorized items
    # Structure: [{"category": "Produce", "items": [{"name": "Bananas", "quantity": "6", "notes": "ripe"}]}]
    items: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Schedule metadata (for recurring trips)
    target_day_name: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'Monday', 'Tuesday', etc.
    time: Mapped[datetime | None] = mapped_column(Time, nullable=True)  # Time of day for shopping
    repeats_every: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Days between occurrences
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    phase: Mapped["Phase | None"] = relationship("Phase", back_populates="grocery_trips")
    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(
        "ScheduleEntry",
        back_populates="grocery_trip",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<GroceryShoppingTrip(id={self.id}, name='{self.name}')>"
