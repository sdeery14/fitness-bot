"""Conversation schemas for API requests and responses."""
from datetime import datetime
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
