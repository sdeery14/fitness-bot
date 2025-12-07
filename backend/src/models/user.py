"""User model."""

from sqlalchemy import Boolean, Column, DateTime, JSON, String
from sqlalchemy.orm import relationship

from src.models import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User account model."""

    __tablename__ = "users"

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # JWT refresh token (FR-054, FR-056)
    refresh_token_hash = Column(String(255), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Profile
    name = Column(String(255), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String(50), nullable=True)  # "male", "female", "non-binary", "prefer not to say"
    height_cm = Column(String(10), nullable=True)  # Stored as string for flexibility
    weight_kg = Column(String(10), nullable=True)  # Stored as string for flexibility

    # Fitness profile
    fitness_level = Column(String(50), nullable=True)  # "beginner", "intermediate", "advanced"
    activity_level = Column(String(50), nullable=True)  # "sedentary", "lightly active", "moderately active", "very active"

    # Dietary restrictions and preferences (FR-046, FR-047)
    dietary_restrictions = Column(JSON, nullable=True)  # ["vegetarian", "gluten-free", "dairy-free", etc.]

    # Equipment access (FR-048)
    equipment_access = Column(JSON, nullable=True)  # ["dumbbells", "barbell", "resistance bands", "home gym", etc.]

    # User preferences (FR-043)
    preferences = Column(JSON, nullable=True)  # {"workout_duration_preference": 45, "meals_per_day": 3, "workout_days_per_week": 4, etc.}

    # Settings
    timezone = Column(String(50), nullable=False, default="UTC")  # IANA timezone string (e.g., "America/New_York", "Europe/London")

    # Relationships
    fitness_plans = relationship("FitnessPlan", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("ProgressRecord", back_populates="user", cascade="all, delete-orphan")
    disruption_events = relationship("DisruptionEvent", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
