"""Exercise Catalog model for curated exercise database."""
from datetime import datetime, timezone as tz
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ExerciseCatalog(Base):
    """Curated exercise catalog for AI agents to query when building workout plans.
    
    This is a standalone catalog independent of user workouts, containing
    200-500 pre-seeded exercises with standardized attributes.
    """

    __tablename__ = "exercise_catalog"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    exercise_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_muscle_groups: Mapped[dict] = mapped_column(JSON, nullable=False)
    equipment_required: Mapped[dict] = mapped_column(JSON, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    form_cues: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    alternatives: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ExerciseCatalog {self.name} ({self.difficulty})>"
