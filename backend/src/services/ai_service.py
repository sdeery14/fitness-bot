"""AI orchestration service for managing multi-agent fitness plan generation.

Coordinates the conversation flow between user and AI agents, manages
handoffs between specialist agents, and handles session persistence.
"""
from agents import Runner
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.agent import PlanContext, UserContext
from src.ai.app_agents.conversation_agent import conversation_agent
from src.ai.app_agents.fitness_plan_agent import create_fitness_plan_agent
from src.ai.app_agents.meal_plan_agent import meal_plan_agent
from src.ai.app_agents.workout_plan_agent import workout_plan_agent
from src.models.user import User
from src.services.conversation_service import ConversationService
from src.services.plan_service import PlanService


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

        # Create fitness plan agent with specialist handoffs
        self.fitness_plan_agent = create_fitness_plan_agent(
            workout_agent=workout_plan_agent,
            meal_agent=meal_plan_agent,
        )

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
                    "conversation_id": session_id,
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

        # Create user context
        user_context = UserContext(
            user_id=str(user.id),
            email=user.email,
            preferences=user.preferences or {},
        )

        # Create plan context
        plan_context = PlanContext(
            user_context=user_context,
            requirements={},
        )

        # If no initial message provided, send AI greeting first
        if not initial_message:
            agent_response = """Hi there! 👋 I'm your AI Fitness Coach, and I'm excited to help you create a personalized fitness plan that fits your goals and lifestyle.

To get started, could you tell me about your primary fitness goal? For example:
• Weight loss
• Muscle gain
• Improved endurance
• Overall health and wellness
• Training for a specific event

What would you like to achieve?"""
        else:
            # Save user's initial message
            await self.conversation_service.add_message(
                conversation_id=db_conversation.id,
                sender_type="user",
                message_content=initial_message,
            )

            # Start conversation with conversation agent (no session, manual history management)
            result = await Runner.run(
                starting_agent=conversation_agent,
                input=initial_message,
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
            model_used="gpt-4",
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
            "conversation_id": session_id,
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
        conversation_id: str,
        user_message: str,
    ) -> dict:
        """Continue an existing conversation.

        Args:
            user: User in the conversation
            conversation_id: Session ID from previous interaction
            user_message: User's message

        Returns:
            Dict with agent_response, status, and updated context
        """
        # Load conversation from database
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

        # Build complete conversation history from database
        conversation_history = []
        for msg in db_conversation.messages:
            conversation_history.append({
                "role": "user" if msg.sender_type == "user" else "assistant",
                "content": msg.message_content,
            })

        # Add the new user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Reconstruct user context
        user_context = UserContext(
            user_id=str(user.id),
            email=user.email,
            preferences=user.preferences or {},
        )

        # Create plan context
        plan_context = PlanContext(
            user_context=user_context,
            requirements={},
        )

        # Save user's message before processing
        await self.conversation_service.add_message(
            conversation_id=db_conversation.id,
            sender_type="user",
            message_content=user_message,
        )

        # Continue conversation with full message history (no session)
        # Pass the entire conversation history as a list of messages
        result = await Runner.run(
            starting_agent=conversation_agent,
            input=conversation_history,  # Pass full conversation history
            context=plan_context,
            session=None,  # Disable session memory, manage history manually
        )

        # Extract response
        agent_response = result.final_output if result.final_output else "I understand. Let me help you with that."

        # Save AI response
        await self.conversation_service.add_message(
            conversation_id=db_conversation.id,
            sender_type="assistant",
            message_content=agent_response,
            model_used="gpt-4",
        )

        # Check if agent has generated a structured plan
        plan_id = None
        if self._is_plan_generated(agent_response):
            # Extract requirements from conversation history
            requirements = await self._extract_requirements_from_conversation(db_conversation)

            # Attempt to trigger structured plan generation
            try:
                plan_result = await self._generate_structured_plan(user, requirements)
                if plan_result and "plan_id" in plan_result:
                    plan_id = plan_result["plan_id"]
                    # Associate plan with conversation
                    await self.conversation_service.update_conversation_status(
                        conversation_id=db_conversation.id,
                        status="completed",
                        context={"plan_id": plan_id, "requirements": requirements},
                    )
            except Exception as e:
                print(f"Warning: Could not generate structured plan: {e}")
                # Continue without failing - user still has text plan

        # Check if requirements are complete (agent indicates readiness to generate plan)
        requirements_complete = self._check_requirements_complete(result)

        # Get the saved messages for response
        from datetime import datetime, UTC
        user_message_time = datetime.now(UTC).isoformat()
        assistant_message_time = datetime.now(UTC).isoformat()

        return {
            "conversation_id": str(db_conversation.id),
            "agent_response": agent_response,
            "status": "plan_generated" if plan_id else ("ready_for_plan" if requirements_complete else "conversation"),
            "context": plan_context.model_dump(),
            "plan_id": plan_id,
            "user_message": {
                "content": user_message,
                "sent_at": user_message_time,
            },
            "assistant_message": {
                "content": agent_response,
                "sent_at": assistant_message_time,
            },
        }

    async def generate_plan(
        self,
        user: User,
        conversation_id: str,
        requirements: dict,
    ) -> dict:
        """Generate a complete fitness plan from gathered requirements.

        Args:
            user: User requesting the plan
            conversation_id: Session ID with conversation history
            requirements: Gathered user requirements

        Returns:
            Dict with plan_id, status, and initial plan data
        """
        # Create plan record in database
        plan = await self.plan_service.create_plan(
            user_id=user.id,
            goal=requirements.get("goal", "general fitness"),
            requirements=requirements,
            duration_weeks=requirements.get("duration_weeks", 12),
        )

        # Create plan context
        user_context = UserContext(
            user_id=str(user.id),
            email=user.email,
            preferences=user.preferences or {},
        )

        plan_context = PlanContext(
            plan_id=str(plan.id),
            user_context=user_context,
            requirements=requirements,
        )

        try:
            # Hand off to fitness plan agent for generation
            result = await Runner.run(
                starting_agent=self.fitness_plan_agent,
                input=f"Generate a complete fitness plan based on these requirements: {requirements}",
                context=plan_context,
                session=None,  # No session needed for plan generation
            )

            # Parse generated plan and save to database
            generated_plan = self._parse_plan_result(result)

            # If we got structured output, save it to database
            if hasattr(result, 'output_data') and result.output_data:
                plan_data = result.output_data.model_dump()
                await self.plan_service.save_generated_plan(
                    plan_id=plan.id,
                    plan_output=plan_data,
                )
            else:
                # Even if no structured output, mark as active
                await self.plan_service.update_plan_status(
                    plan_id=plan.id,
                    status="active",
                )

            return {
                "plan_id": str(plan.id),
                "status": "completed",
                "plan_data": generated_plan,
            }

        except Exception as e:
            # Update plan status to failed
            await self.plan_service.update_plan_status(
                plan_id=plan.id,
                status="abandoned",
                error_message=str(e),
            )

            return {
                "plan_id": str(plan.id),
                "status": "failed",
                "error": str(e),
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
        if hasattr(result, 'output_data') and result.output_data:
            return result.output_data.model_dump()

        # Fallback to raw text output
        if not result.final_output:
            return {"error": "No plan generated"}

        return {
            "raw_output": result.final_output,
            "type": "text",
        }

    def _is_plan_generated(self, agent_response: str) -> bool:
        """Check if the agent response contains a generated plan.

        Args:
            agent_response: AI agent's response text

        Returns:
            True if response contains a plan, False otherwise
        """
        # Check for plan indicators in the response
        plan_indicators = [
            "weekly split",
            "day 1:",
            "workout structure",
            "meal plan",
            "here's your",
            "personalized plan",
            "fitness plan",
        ]

        content_lower = agent_response.lower()
        return any(indicator in content_lower for indicator in plan_indicators) and len(agent_response) > 500

    async def _extract_requirements_from_conversation(self, conversation) -> dict:
        """Extract user requirements from conversation messages.

        Args:
            conversation: Conversation object with messages

        Returns:
            Dict of extracted requirements
        """
        # Analyze conversation to extract key information
        requirements = {
            "goal": "general fitness",
            "fitness_level": "beginner",
            "frequency_per_week": 3,
            "duration_weeks": 12,
        }

        # Parse messages for requirements
        for msg in conversation.messages:
            if msg.sender_type == "user":
                content = msg.message_content.lower()

                # Extract goal
                if "muscle" in content or "build" in content:
                    requirements["goal"] = "muscle_gain"
                elif "lose" in content or "weight loss" in content or "fat" in content:
                    requirements["goal"] = "weight_loss"
                elif "endurance" in content or "cardio" in content:
                    requirements["goal"] = "endurance"

                # Extract fitness level
                if "beginner" in content:
                    requirements["fitness_level"] = "beginner"
                elif "intermediate" in content:
                    requirements["fitness_level"] = "intermediate"
                elif "advanced" in content:
                    requirements["fitness_level"] = "advanced"

                # Extract frequency
                for i in range(2, 8):
                    if f"{i} day" in content or f"{i} time" in content:
                        requirements["frequency_per_week"] = i
                        break

                # Extract equipment access
                if "gym" in content:
                    requirements["equipment_access"] = "full_gym"
                elif "home" in content and ("dumbbell" in content or "equipment" in content):
                    requirements["equipment_access"] = "home_gym"
                elif "bodyweight" in content or "no equipment" in content:
                    requirements["equipment_access"] = "bodyweight"

        return requirements

    async def _generate_structured_plan(self, user: User, requirements: dict) -> dict | None:
        """Generate and save a structured fitness plan.

        Args:
            user: User requesting the plan
            requirements: Extracted requirements from conversation

        Returns:
            Dict with plan_id and status, or None if generation fails
        """
        try:
            # Create plan record
            plan = await self.plan_service.create_plan(
                user_id=user.id,
                goal=requirements.get("goal", "general_fitness"),
                requirements=requirements,
                duration_weeks=requirements.get("duration_weeks", 12),
            )

            # Create plan context
            user_context = UserContext(
                user_id=str(user.id),
                email=user.email,
                preferences=user.preferences or {},
            )

            plan_context = PlanContext(
                plan_id=str(plan.id),
                user_context=user_context,
                requirements=requirements,
            )

            # Generate structured plan using fitness plan agent
            result = await Runner.run(
                starting_agent=self.fitness_plan_agent,
                input=f"Generate a structured fitness plan for: {requirements}",
                context=plan_context,
                session=None,
            )

            # Extract structured output
            if hasattr(result, 'output_data') and result.output_data:
                # Convert Pydantic model to dict for storage
                plan_data = result.output_data.model_dump()

                # Save the complete plan to database
                await self.plan_service.save_generated_plan(
                    plan_id=plan.id,
                    plan_output=plan_data,
                )

                return {
                    "plan_id": str(plan.id),
                    "status": "completed",
                    "plan_data": plan_data,
                }

            # If no structured output, mark as active with text only
            await self.plan_service.update_plan_status(
                plan_id=plan.id,
                status="active",
            )

            return {
                "plan_id": str(plan.id),
                "status": "completed_text_only",
            }

        except Exception as e:
            print(f"Error generating structured plan: {e}")
            return None

