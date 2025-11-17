"""Conversation and message models."""

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.models import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    """Conversation model for AI interactions (FR-063, FR-071)."""

    __tablename__ = "conversations"

    # User association
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional fitness plan association (conversations can happen before plan creation)
    fitness_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="CASCADE"), nullable=True, index=True)

    # Conversation metadata
    conversation_type = Column(
        Enum("plan_creation", "plan_update", "general_question", name="conversation_type"),
        nullable=False,
    )
    status = Column(
        Enum("active", "completed", "abandoned", name="conversation_status"),
        nullable=False,
        default="active",
    )

    # Conversation context (stored in Redis during active conversation, persisted here on completion)
    conversation_context = Column(JSON, nullable=True)
    # Structure: {
    #   "user_requirements": {...},
    #   "clarifications_needed": [...],
    #   "current_step": "...",
    #   "agent_references": {...}  # Storage references for agent state
    # }

    # Relationships
    user = relationship("User", back_populates="conversations")
    fitness_plan = relationship("FitnessPlan", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    disruption_events = relationship("DisruptionEvent", back_populates="conversation")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, type={self.conversation_type})>"


class Message(Base, UUIDMixin, TimestampMixin):
    """Message model for conversation history (FR-072, FR-073)."""

    __tablename__ = "messages"

    # Conversation association
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message metadata
    sender_type = Column(
        Enum("user", "assistant", "system", name="sender_type"),
        nullable=False,
    )

    # Message content
    message_content = Column(Text, nullable=False)

    # AI metadata (for assistant messages)
    model_used = Column(String(100), nullable=True)  # "gpt-4", "gpt-3.5-turbo", etc.
    function_calls = Column(JSON, nullable=True)  # Record of tool/function calls made

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, sender={self.sender_type})>"


class DisruptionEvent(Base, UUIDMixin, TimestampMixin):
    """Disruption event model for tracking schedule disruptions and rescheduling (FR-016, FR-017, FR-018)."""

    __tablename__ = "disruption_events"

    # User and plan associations
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    fitness_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Disruption details
    disruption_type = Column(
        Enum("illness", "injury", "travel", "schedule_conflict", "other", name="disruption_type"),
        nullable=False,
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # null means ongoing
    description = Column(Text, nullable=False)
    
    # Severity assessment (impacts rescheduling strategy)
    severity = Column(
        Enum("minor", "moderate", "severe", name="disruption_severity"),
        nullable=False,
        default="moderate",
    )

    # Impact tracking
    workouts_affected = Column(Integer, nullable=False, default=0)
    meals_affected = Column(Integer, nullable=False, default=0)

    # Resolution details
    resolution_strategy = Column(
        Enum("reschedule", "skip", "extend_timeline", "reassess", name="resolution_strategy"),
        nullable=False,
    )
    timeline_extension_days = Column(Integer, nullable=False, default=0)
    
    # Additional metadata
    resolution_details = Column(JSON, nullable=True)
    # Structure: {
    #   "rescheduled_workouts": [...],
    #   "rescheduled_meals": [...],
    #   "new_end_date": "...",
    #   "ai_recommendations": "..."
    # }

    # Status tracking
    status = Column(
        Enum("reported", "processing", "resolved", name="disruption_status"),
        nullable=False,
        default="reported",
    )

    # Relationships
    user = relationship("User", back_populates="disruption_events")
    conversation = relationship("Conversation")
    fitness_plan = relationship("FitnessPlan", back_populates="disruption_events")

    def __repr__(self) -> str:
        return f"<DisruptionEvent(id={self.id}, type={self.disruption_type}, status={self.status})>"
