"""AI orchestration service for managing multi-agent fitness plan generation.

Coordinates the conversation flow between user and AI agents, manages
handoffs between specialist agents, and handles session persistence.
"""
import json
from datetime import datetime

from agents import Runner
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.agent import PlanContext, UserContext
from src.ai.app_agents.conversation_agent import conversation_agent
from src.ai.app_agents.intake_specialist_agent import intake_specialist_agent
from src.config import settings
from src.models.user import User
from src.services.conversation_service import ConversationService
from src.services.plan_service import PlanService
from src.utils.date_utils import get_current_datetime


class AIOrchestrationService:
    """Service for orchestrating AI agent interactions."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize AI orchestration service.

        Args:
            db: Database session for plan persistence
        """
        self.db = db
        self.plan_service = PlanService(db)
        self.conversation_service = ConversationService(db)

    async def start_conversation(
        self,
        user: User,
        initial_message: str,
        session_id: str | None = None,
        force_new: bool = False,
    ) -> dict:
        """Start a new fitness planning conversation.

        Args:
            user: User starting the conversation
            initial_message: User's initial message/goal
            session_id: Optional existing session ID to resume
            force_new: If True, always create a new conversation without loading history

        Returns:
            Dict with conversation_id, agent_response, and status
        """
        # Generate session ID - use unique ID when forcing new conversation
        if not session_id:
            if force_new:
                import uuid
                session_id = f"user_{user.id}_session_{uuid.uuid4()}"
            else:
                session_id = f"user_{user.id}_session"

        # Check if an active conversation already exists (skip if forcing new)
        db_conversation = None
        if not force_new:
            db_conversation = await self.conversation_service.get_conversation_by_session_id(
                session_id=session_id,
                load_messages=True,
            )

        # If conversation exists with messages and we're not forcing new, return it with full history
        if db_conversation and db_conversation.messages:
            last_message = db_conversation.messages[-1]
            if last_message.sender_type == "assistant":
                # Build message history
                message_history = [
                    {
                        "id": str(msg.id),
                        "sender_type": msg.sender_type,
                        "message_content": msg.message_content,
                        "created_at": msg.created_at.isoformat(),
                    }
                    for msg in db_conversation.messages
                ]
                return {
                    "conversation_id": str(db_conversation.id),  # Return DB UUID, not session ID
                    "conversation_type": db_conversation.conversation_type,
                    "agent_response": last_message.message_content,
                    "status": db_conversation.status,
                    "started_at": db_conversation.created_at.isoformat() if db_conversation.created_at else None,
                    "context": db_conversation.conversation_context or {},
                    "message_history": message_history,
                }

        # Create new conversation if none exists
        if not db_conversation:
            db_conversation = await self.conversation_service.create_conversation(
                user_id=user.id,
                conversation_type="plan_creation",
            )

        # Get current datetime in user's timezone
        user_timezone = user.timezone or "UTC"
        current_dt = get_current_datetime(user_timezone)
        
        # Create user context
        user_context = UserContext(
            user_id=str(user.id),
            email=user.email,
            preferences=user.preferences or {},
        )

        # Check if user has existing fitness plans to determine which agent to use
        has_plans = await self.plan_service.has_existing_plans(user.id)

        # Select appropriate agent based on user's history
        # New users (no plans) get the intake specialist for smooth onboarding
        # Existing users get the conversation agent for plan management
        selected_agent = conversation_agent if has_plans else intake_specialist_agent

        # Create plan context
        plan_context = PlanContext(
            user_context=user_context,
            requirements={},
        )

        # If no initial message provided, send AI greeting first
        if not initial_message:
            # Customize greeting based on whether user is new or returning
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
        else:
            # Save user's initial message
            await self.conversation_service.add_message(
                conversation_id=db_conversation.id,
                sender_type="user",
                message_content=initial_message,
            )

            # Build context-aware input with datetime information
            contextual_input = f"""Current Date and Time: {current_dt.strftime('%A, %B %d, %Y at %I:%M %p')} ({user_timezone})
User Message: {initial_message}"""
            
            # Start conversation with selected agent
            result = await Runner.run(
                starting_agent=selected_agent,
                input=contextual_input,
                context=plan_context,
                session=None,  # Disable session memory, manage history manually
            )

            # Extract response from result
            agent_response = result.final_output if result.final_output else "Hello! I'm here to help you create a personalized fitness plan."

        # Save AI response
        await self.conversation_service.add_message(
            conversation_id=db_conversation.id,
            sender_type="assistant",
            message_content=agent_response,
            model_used=settings.MODEL_NAME,
        )

        # Re-fetch conversation with messages to get proper IDs and timestamps
        db_conversation_with_msgs = await self.conversation_service.get_conversation(
            conversation_id=db_conversation.id,
            load_messages=True,
        )

        # Build message history for response - only include messages from THIS conversation
        message_history = []
        if db_conversation_with_msgs and db_conversation_with_msgs.messages:
            # If no initial message, only include the AI greeting (last 1 message)
            # Otherwise include both user message and AI response (last 2 messages)
            num_messages = 1 if not initial_message else 2
            for msg in db_conversation_with_msgs.messages[-num_messages:]:
                message_history.append({
                    "id": str(msg.id),
                    "sender_type": msg.sender_type,
                    "message_content": msg.message_content,
                    "created_at": msg.created_at.isoformat(),
                })

        return {
            "conversation_id": str(db_conversation.id),  # Return DB UUID, not session ID
            "conversation_type": db_conversation.conversation_type,
            "agent_response": agent_response,
            "status": db_conversation.status,
            "started_at": db_conversation.created_at.isoformat() if db_conversation.created_at else None,
            "context": plan_context.model_dump(),
            "message_history": message_history,
        }

    async def continue_conversation(
        self,
        user: User,
        conversation_id: str | None,
        user_message: str,
        timezone_override: str | None = None,
    ) -> dict:
        """Continue an existing conversation or create new one on first message.

        Args:
            user: User in the conversation
            conversation_id: Conversation ID (None for first message)
            user_message: User's message
            timezone_override: Optional timezone to override user's stored timezone for this message

        Returns:
            Dict with agent_response, status, and updated context
        """
        # Load or create conversation
        db_conversation = None
        
        if conversation_id:
            # Load existing conversation from database
            from uuid import UUID
            try:
                conversation_uuid = UUID(conversation_id)
                db_conversation = await self.conversation_service.get_conversation(
                    conversation_id=conversation_uuid,
                    load_messages=True,
                )
            except ValueError:
                # If not a valid UUID, try session_id format
                db_conversation = await self.conversation_service.get_conversation_by_session_id(
                    session_id=conversation_id,
                    load_messages=True,
                )

            if not db_conversation:
                raise ValueError(f"Conversation not found: {conversation_id}")

        # Build complete conversation history from database messages (empty for new conversations)
        conversation_history = []
        if db_conversation:
            for msg in db_conversation.messages:
                conversation_history.append({
                    "role": "user" if msg.sender_type == "user" else "assistant",
                    "content": msg.message_content,
                })

        # Get current datetime in user's timezone (use override if provided)
        user_timezone = timezone_override or user.timezone or "UTC"
        current_dt = get_current_datetime(user_timezone)
        
        # Reconstruct user context
        user_context = UserContext(
            user_id=str(user.id),
            email=user.email,
            preferences=user.preferences or {},
        )

        # Create plan context with conversation history
        plan_context = PlanContext(
            user_context=user_context,
            requirements={},
            conversation_history=conversation_history,  # Pass full conversation history through context
        )

        # Check if user has existing fitness plans to determine which agent to use
        has_plans = await self.plan_service.has_existing_plans(user.id)
        selected_agent = conversation_agent if has_plans else intake_specialist_agent

        # For new conversations, create with title from user message before running agent
        # This allows plan tools to insert plan messages during execution
        is_new_conversation = db_conversation is None
        if is_new_conversation:
            from src.services.title_generation_service import generate_conversation_title
            
            # Generate title from user's first message only
            title = await generate_conversation_title(user_message, "")
            
            db_conversation = await self.conversation_service.create_conversation(
                user_id=user.id,
                conversation_type="plan_creation",
                title=title,
            )

        # Save user's message BEFORE running agent to ensure correct timestamp order
        await self.conversation_service.add_message(
            conversation_id=db_conversation.id,
            sender_type="user",
            message_content=user_message,
        )

        # Set context for plan tools (enables database persistence)
        from src.ai.tools.plan_tools import set_plan_tools_context, clear_plan_tools_context

        set_plan_tools_context(
            user_id=user.id,
            db_session=self.db,
            conversation_id=db_conversation.id
        )

        try:
            # Continue conversation with the new user message
            # Build context-aware input with datetime information
            contextual_message = f"""Current Date and Time: {current_dt.strftime('%A, %B %d, %Y at %I:%M %p')} ({user_timezone})
User Message: {user_message}"""
            
            # Append contextual user message to conversation history
            conversation_input = conversation_history + [{"role": "user", "content": contextual_message}]
            
            result = await Runner.run(
                starting_agent=selected_agent,
                input=conversation_input,  # Pass full conversation history including new message
                session=None,  # Disable session memory, manage history manually
            )
        finally:
            # Always clear context to prevent leakage between requests
            clear_plan_tools_context()

        # Extract response
        agent_response = result.final_output if result.final_output else "I understand. Let me help you with that."

        # For new conversations, generate and update the title
        if is_new_conversation:
            from src.services.title_generation_service import generate_conversation_title
            
            # Generate title from first exchange
            title = await generate_conversation_title(user_message, agent_response)
            
            # Update conversation with generated title
            db_conversation.title = title
            await self.db.commit()

        # Save AI response
        await self.conversation_service.add_message(
            conversation_id=db_conversation.id,
            sender_type="assistant",
            message_content=agent_response,
            model_used=settings.MODEL_NAME,
        )

        # Note: Plan generation is now handled directly by the conversation_agent
        # via the build_fitness_plan tool. No need for post-processing.
        
        # Check if requirements are complete (agent indicates readiness to generate plan)
        requirements_complete = self._check_requirements_complete(result)

        # Get the saved messages for response
        from datetime import datetime, UTC
        user_message_time = datetime.now(UTC).isoformat()
        assistant_message_time = datetime.now(UTC).isoformat()

        return {
            "conversation_id": str(db_conversation.id),
            "agent_response": agent_response,
            "status": "ready_for_plan" if requirements_complete else "conversation",
            "context": plan_context.model_dump(),
            "user_message": {
                "content": user_message,
                "sent_at": user_message_time,
            },
            "assistant_message": {
                "content": agent_response,
                "sent_at": assistant_message_time,
            },
        }

    def _check_requirements_complete(self, result) -> bool:
        """Check if conversation agent has gathered sufficient requirements.

        Args:
            result: Runner result from conversation

        Returns:
            True if ready to generate plan, False if more conversation needed
        """
        # Check if agent's response indicates readiness
        # This is a heuristic - look for confirmation keywords
        if not result.final_output:
            return False

        content = result.final_output.lower()

        # Keywords indicating readiness
        readiness_keywords = [
            "ready to generate",
            "ready to create",
            "sufficient information",
            "have everything",
            "let me create",
            "i'll create",
        ]

        return any(keyword in content for keyword in readiness_keywords)

    def _parse_plan_result(self, result) -> dict:
        """Parse the fitness plan agent's result into structured data.

        Args:
            result: Runner result from fitness plan agent

        Returns:
            Structured plan data dictionary
        """
        # Check if we have structured output (Pydantic model)
        # When agent has output_type defined, final_output contains the structured object
        if result.final_output and hasattr(result.final_output, 'model_dump'):
            return result.final_output.model_dump()

        # Fallback to raw text output (if agent didn't have output_type)
        if not result.final_output:
            return {"error": "No plan generated"}

        # If final_output is a string
        if isinstance(result.final_output, str):
            return {
                "raw_output": result.final_output,
                "type": "text",
            }

        # If final_output is already a dict or other object
        return result.final_output
