"""Base models with common fields and mixins."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declarative_mixin

# Create Base for all models
Base = declarative_base()


@declarative_mixin
class UUIDMixin:
    """Mixin for UUID primary key."""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


@declarative_mixin
class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# Import all models for Alembic autogenerate
from src.models.user import User  # noqa: E402, F401
from src.models.fitness_plan import FitnessPlan, Phase  # noqa: E402, F401
from src.models.workout import WorkoutPlan, Workout, Exercise  # noqa: E402, F401
from src.models.meal import MealPlan, Meal  # noqa: E402, F401
from src.models.conversation import Conversation, Message  # noqa: E402, F401
