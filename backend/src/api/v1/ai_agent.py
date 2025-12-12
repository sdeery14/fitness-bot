"""AI agent conversation endpoints."""
import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.api.deps import CurrentUserId, DatabaseSession
from src.schemas import create_success_response
from src.schemas.conversation import DisruptionReportRequest, DisruptionResolutionResponse
from src.services.ai_service import AIOrchestrationService
from src.services.plan_service import PlanService
from src.services.schedule_service import ScheduleService
from src.services.user_service import UserService
from src.models.conversation import DisruptionEvent

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
    timezone: str | None = None  # Optional: override user's stored timezone for this message


class MessageResponse(BaseModel):
    """Message response."""

    agent_response: str
    status: str
    context: dict


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def start_conversation(
    request: StartConversationRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get initial AI greeting without creating conversation in DB.
    
    Conversation is only created when user sends their first message.

    Args:
        request: Initial message (unused - always returns greeting)
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        AI greeting message (no conversation_id yet)

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        plan_service = PlanService(db)
        has_plans = await plan_service.has_existing_plans(user.id)

        # Return appropriate greeting based on user's history
        if has_plans:
            agent_response = """Welcome back! I'm your AI fitness coach, ready to help you with your fitness journey.

How can I assist you today?
• Discuss your current plan
• Make modifications to your workouts or meals
• Start a fresh plan with a new goal
• Get advice on your progress

What would you like to work on?"""
        else:
            agent_response = """Welcome! I'm thrilled to help you start your fitness journey! 🎉

You can click one of the quick-start options above to fill in a template (which you can customize), or tell me about your fitness goals in your own words.

Either way, I'm here to help you succeed!"""

        return create_success_response({
            "agent_response": agent_response,
            "conversation_id": None,  # No conversation created yet
            "status": "greeting",
            "message_history": [{
                "id": "greeting",
                "sender_type": "assistant",
                "message_content": agent_response,
                "created_at": None,
            }],
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in start_conversation: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}",
        ) from e


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Send a message - creates conversation on first user message.

    Args:
        conversation_id: Conversation ID (use "new" for first message)
        request: User message
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Agent response with conversation_id

    Raises:
        HTTPException: If user not found or send fails
    """
    # Validate message is not empty
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )
    
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    ai_service = AIOrchestrationService(db)

    try:
        # Check if this is a first message (conversation_id == "new")
        is_first_message = conversation_id == "new"
        actual_conversation_id = None if is_first_message else conversation_id

        result = await ai_service.continue_conversation(
            user=user,
            conversation_id=actual_conversation_id,
            user_message=request.message,
            timezone_override=request.timezone,
        )

        # Generate a message_id (could use UUID from database message in future)
        import uuid
        message_id = str(uuid.uuid4())
        
        # Extract the assistant message content from the result
        assistant_message_content = result["assistant_message"]["content"] if isinstance(result.get("assistant_message"), dict) else result.get("agent_response", "")
        
        # Title is generated automatically in ai_service for new conversations
        
        return create_success_response({
            "message_id": message_id,
            "conversation_id": result["conversation_id"],
            "user_message": result["user_message"],
            "assistant_response": assistant_message_content,
        })

    except ValueError as e:
        # Conversation not found or invalid state
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in send_message: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        ) from e


@router.get("/conversations")
async def list_conversations(
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> dict:
    """List all conversations for the current user.

    Args:
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        List of user's conversations

    Raises:
        HTTPException: If retrieval fails
    """
    from src.models.conversation import Conversation
    from sqlalchemy import select
    
    try:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await db.execute(stmt)
        conversations = result.scalars().all()
        
        return create_success_response({
            "conversations": [
                {
                    "id": str(conv.id),
                    "title": conv.title,
                    "status": conv.status,
                    "conversation_type": conv.conversation_type,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                }
                for conv in conversations
            ]
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
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
    from src.schemas import create_error_response
    from src.services.conversation_service import ConversationService

    try:
        conv_service = ConversationService(db)
        conversation = await conv_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    code="NOT_FOUND",
                    message=f"Conversation {conversation_id} not found"
                )
            )
        
        # Check authorization
        if str(conversation.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation"
            )
        
        return create_success_response({
            "id": str(conversation.id),
            "conversation_id": str(conversation.id),
            "user_id": str(conversation.user_id),
            "status": conversation.status,
            "conversation_type": conversation.conversation_type,
            "messages": [],  # Would retrieve from Message model in full implementation
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        ) from e


@router.get("/conversations/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> StreamingResponse:
    """Stream AI responses in real-time (SSE).

    Args:
        conversation_id: Conversation ID
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Server-Sent Events stream

    Raises:
        HTTPException: If conversation not found

    Note:
        For MVP, this returns a simple SSE stream.
        Full implementation would integrate with OpenAI streaming API.
    """
    from src.services.conversation_service import ConversationService

    # Validate conversation exists and user has access
    conv_service = ConversationService(db)
    conversation = await conv_service.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    if str(conversation.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation"
        )

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


@router.post("/reschedule", status_code=status.HTTP_200_OK)
async def reschedule_for_disruption(
    request: DisruptionReportRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> dict:
    """Report a disruption and reschedule the fitness plan (FR-016, FR-017, FR-018).

    Allows users to report unexpected life events (illness, injury, travel, etc.)
    and intelligently reschedules their plan to accommodate the disruption.

    Args:
        request: Disruption details (type, dates, severity, description)
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Rescheduling result with affected items and new timeline

    Raises:
        HTTPException: If user/plan not found or rescheduling fails
    """
    # Validate user exists
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate fitness plan exists and belongs to user
    plan_service = PlanService(db)
    plan = await plan_service.get_plan(request.fitness_plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness plan not found",
        )

    if str(plan.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this plan",
        )

    try:
        # Create disruption event
        from uuid import uuid4
        disruption = DisruptionEvent(
            id=uuid4(),
            user_id=user_id,
            fitness_plan_id=request.fitness_plan_id,
            disruption_type=request.disruption_type,
            start_date=request.start_date,
            end_date=request.end_date,
            description=request.description,
            severity=request.severity,
            resolution_strategy="reschedule",  # Will be updated by service
            status="processing",
        )
        db.add(disruption)
        await db.flush()  # Get disruption ID

        # Execute rescheduling synchronously for immediate response
        # (For complex cases, could queue to Celery worker instead)
        schedule_service = ScheduleService(db)
        result = await schedule_service.reschedule_for_disruption(disruption)

        # Update disruption with results
        disruption.workouts_affected = result["workouts_affected"]
        disruption.meals_affected = result["meals_affected"]
        disruption.timeline_extension_days = result["timeline_extension_days"]
        disruption.resolution_strategy = result["strategy_applied"]
        disruption.resolution_details = {
            "rescheduled_workouts": result["rescheduled_workouts"],
            "rescheduled_meals": result["rescheduled_meals"],
            "new_end_date": result["new_end_date"].isoformat() if result["new_end_date"] else None,
        }
        disruption.status = "resolved"

        await db.commit()
        await db.refresh(disruption)

        # Build response
        response = DisruptionResolutionResponse(
            disruption_id=disruption.id,
            resolution_strategy=result["strategy_applied"],
            workouts_affected=result["workouts_affected"],
            meals_affected=result["meals_affected"],
            timeline_extension_days=result["timeline_extension_days"],
            new_end_date=result["new_end_date"],
            resolution_details=disruption.resolution_details,
            ai_message=f"I've rescheduled your plan to accommodate your {request.disruption_type}. "
                       f"Affected: {result['workouts_affected']} workouts, {result['meals_affected']} meals. "
                       + (f"Extended timeline by {result['timeline_extension_days']} days to {result['new_end_date'].strftime('%B %d, %Y')}." if result['timeline_extension_days'] > 0 else "No timeline extension needed - items rescheduled within current plan duration."),
            status="resolved",
            created_at=disruption.created_at,
            updated_at=disruption.updated_at,
        )

        return create_success_response(response.model_dump())

    except ValueError as e:
        # Schedule or plan issues
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        # Rollback on error
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule plan: {str(e)}",
        ) from e
