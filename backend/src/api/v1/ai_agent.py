"""AI agent conversation endpoints."""
import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.api.deps import CurrentUserId, DatabaseSession
from src.services.ai_service import AIOrchestrationService
from src.services.plan_service import PlanService
from src.services.user_service import UserService

router = APIRouter()


class StartConversationRequest(BaseModel):
    """Start conversation request."""

    initial_message: str | None = None  # Optional: if None, AI initiates with greeting
    force_new: bool = False  # Force create a new conversation instead of resuming


class MessageHistoryItem(BaseModel):
    """Message history item."""

    id: str
    sender_type: str
    message_content: str
    created_at: str


class ConversationResponse(BaseModel):
    """Conversation response."""

    conversation_id: str
    agent_response: str
    status: str  # "conversation" or "ready_for_plan"
    context: dict
    message_history: list[MessageHistoryItem] = []  # Full conversation history


class SendMessageRequest(BaseModel):
    """Send message request."""

    message: str


class MessageResponse(BaseModel):
    """Message response."""

    agent_response: str
    status: str
    context: dict


class GeneratePlanRequest(BaseModel):
    """Generate plan request."""

    requirements: dict


class GeneratePlanResponse(BaseModel):
    """Generate plan response."""

    plan_id: str
    status: str  # "completed" or "failed"
    plan_data: dict | None = None
    error: str | None = None


@router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    request: StartConversationRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> ConversationResponse:
    """Start a new AI conversation for fitness planning.

    Args:
        request: Initial message
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Conversation ID and agent response

    Raises:
        HTTPException: If user not found or conversation fails
    """
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    ai_service = AIOrchestrationService(db)

    try:
        result = await ai_service.start_conversation(
            user=user,
            initial_message=request.initial_message,
            force_new=request.force_new,
        )

        return ConversationResponse(**result)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in start_conversation: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}",
        ) from e


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> MessageResponse:
    """Send a message in an existing conversation.

    Args:
        conversation_id: Conversation ID
        request: User message
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Agent response

    Raises:
        HTTPException: If conversation not found or send fails
    """
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    ai_service = AIOrchestrationService(db)

    try:
        result = await ai_service.continue_conversation(
            user=user,
            conversation_id=conversation_id,
            user_message=request.message,
        )

        return MessageResponse(
            agent_response=result["agent_response"],
            status=result["status"],
            context=result["context"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        ) from e


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> dict:
    """Get conversation details (placeholder for MVP).

    Args:
        conversation_id: Conversation ID
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Conversation details

    Raises:
        HTTPException: If conversation not found
    """
    # For MVP, return basic info
    # In full implementation, would retrieve from Conversation model
    return {
        "conversation_id": conversation_id,
        "user_id": str(user_id),
        "status": "active",
        "messages": [],  # Would retrieve from Message model
    }


@router.post("/conversations/{conversation_id}/generate-plan", response_model=GeneratePlanResponse)
async def generate_plan(
    conversation_id: str,
    request: GeneratePlanRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> GeneratePlanResponse:
    """Generate a fitness plan from conversation requirements.

    Args:
        conversation_id: Conversation ID
        request: Gathered requirements
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Generated plan ID and status

    Raises:
        HTTPException: If generation fails
    """
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    plan_service = PlanService(db)
    ai_service = AIOrchestrationService(db, plan_service)

    try:
        result = await ai_service.generate_plan(
            user=user,
            conversation_id=conversation_id,
            requirements=request.requirements,
        )

        return GeneratePlanResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate plan: {str(e)}",
        ) from e


@router.get("/conversations/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    user_id: CurrentUserId,
) -> StreamingResponse:
    """Stream AI responses in real-time (SSE).

    Args:
        conversation_id: Conversation ID
        user_id: Current authenticated user ID

    Returns:
        Server-Sent Events stream

    Note:
        For MVP, this returns a simple SSE stream.
        Full implementation would integrate with OpenAI streaming API.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        # For MVP, simulate streaming
        # In full implementation, would stream from OpenAI Agents SDK
        yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"

        await asyncio.sleep(0.1)
        yield f"data: {json.dumps({'type': 'message', 'content': 'Processing your request...'})}\n\n"

        await asyncio.sleep(0.1)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
