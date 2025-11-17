"""Conversation schemas for API requests and responses."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    message_content: str = Field(..., min_length=1, max_length=10000, description="Message content from user")


class MessageRead(BaseModel):
    """Schema for message response."""

    id: UUID
    conversation_id: UUID
    sender_type: str = Field(..., description="Sender: user, assistant, system")
    message_content: str
    model_used: Optional[str] = Field(None, description="AI model used for assistant messages")
    function_calls: Optional[dict] = Field(None, description="Tool/function calls made by assistant")
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    conversation_type: str = Field(
        ...,
        pattern="^(plan_creation|plan_update|general_question)$",
        description="Conversation type",
    )
    fitness_plan_id: Optional[UUID] = Field(None, description="Associated fitness plan (null for new plan creation)")


class ConversationRead(BaseModel):
    """Schema for conversation response."""

    id: UUID
    user_id: UUID
    fitness_plan_id: Optional[UUID]
    conversation_type: str
    status: str = Field(..., description="Status: active, completed, abandoned")
    conversation_context: Optional[dict] = Field(None, description="Conversation context and agent state")
    messages: list[MessageRead] = Field(default_factory=list, description="Conversation messages")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DisruptionReportRequest(BaseModel):
    """Schema for reporting a schedule disruption (FR-016, FR-017, FR-018)."""

    fitness_plan_id: UUID = Field(..., description="Fitness plan affected by disruption")
    disruption_type: str = Field(
        ...,
        pattern="^(illness|injury|travel|schedule_conflict|other)$",
        description="Type of disruption",
    )
    start_date: date = Field(..., description="Date when disruption started")
    end_date: Optional[date] = Field(None, description="Expected end date (null if ongoing)")
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Detailed description of the disruption",
    )
    severity: str = Field(
        "moderate",
        pattern="^(minor|moderate|severe)$",
        description="Severity assessment",
    )


class DisruptionResolutionResponse(BaseModel):
    """Schema for disruption resolution response from AI (FR-016, FR-017, FR-018)."""

    disruption_id: UUID = Field(..., description="ID of the disruption event")
    resolution_strategy: str = Field(
        ...,
        pattern="^(reschedule|skip|extend_timeline|reassess)$",
        description="Resolution strategy applied",
    )
    workouts_affected: int = Field(..., description="Number of workouts affected")
    meals_affected: int = Field(..., description="Number of meals affected")
    timeline_extension_days: int = Field(0, description="Days added to plan timeline")
    new_end_date: Optional[date] = Field(None, description="New plan end date if timeline extended")
    resolution_details: dict = Field(
        default_factory=dict,
        description="Detailed information about rescheduled items and AI recommendations",
    )
    ai_message: str = Field(..., description="Human-readable explanation from AI about the resolution")
    status: str = Field(
        "resolved",
        pattern="^(reported|processing|resolved)$",
        description="Status of the disruption",
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
