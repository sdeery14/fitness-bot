"""Conversation service for managing conversation and message persistence."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation, Message


class ConversationService:
    """Service for managing conversations and messages."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize conversation service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_conversation(
        self,
        user_id: UUID,
        conversation_type: str = "plan_creation",
        fitness_plan_id: UUID | None = None,
        title: str = "New Conversation",
    ) -> Conversation:
        """Create a new conversation.

        Args:
            user_id: User ID
            conversation_type: Type of conversation (plan_creation, plan_update, general_question)
            fitness_plan_id: Optional fitness plan ID to associate
            title: Conversation title (will be auto-generated after first message)

        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            conversation_type=conversation_type,
            fitness_plan_id=fitness_plan_id,
            status="active",
            conversation_context={},
            title=title,
        )

        self.db.add(conversation)
        await self.db.commit()
        # Note: refresh not needed after commit - the object is already in the session
        
        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        load_messages: bool = True,
    ) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation ID
            load_messages: Whether to eagerly load messages

        Returns:
            Conversation or None if not found
        """
        query = select(Conversation).where(Conversation.id == conversation_id)

        if load_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_conversation_by_session_id(
        self,
        session_id: str,
        load_messages: bool = True,
    ) -> Conversation | None:
        """Get a conversation by session ID (format: user_{user_id}_session).

        Args:
            session_id: Session ID from agents framework
            load_messages: Whether to eagerly load messages

        Returns:
            Conversation or None if not found
        """
        # Extract user_id from session_id format: "user_{uuid}_session"
        if not session_id.startswith("user_") or not session_id.endswith("_session"):
            return None

        user_id_str = session_id.replace("user_", "").replace("_session", "")
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            return None

        # Get the most recent active conversation for this user
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.status == "active")
            .order_by(Conversation.created_at.desc())
            .limit(1)  # Only get the most recent one
        )

        if load_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: UUID,
        sender_type: str,
        message_content: str,
        model_used: str | None = None,
        function_calls: dict | None = None,
        plan_id: UUID | None = None,
    ) -> Message:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            sender_type: Message sender (user, assistant, system, plan)
            message_content: Message text
            model_used: AI model used (for assistant messages)
            function_calls: Function calls made (for assistant messages)
            plan_id: Plan ID (for plan messages)

        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            message_content=message_content,
            model_used=model_used,
            function_calls=function_calls,
            plan_id=plan_id,
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        limit: int | None = None,
    ) -> list[Message]:
        """Get messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Optional limit on number of messages

        Returns:
            List of messages ordered by creation time
        """
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_conversation_status(
        self,
        conversation_id: UUID,
        status: str,
        context: dict | None = None,
    ) -> Conversation | None:
        """Update conversation status and context.

        Args:
            conversation_id: Conversation ID
            status: New status (active, completed, abandoned)
            context: Optional updated context

        Returns:
            Updated conversation or None if not found
        """
        conversation = await self.get_conversation(conversation_id, load_messages=False)

        if not conversation:
            return None

        conversation.status = status
        if context is not None:
            conversation.conversation_context = context

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def get_user_conversations(
        self,
        user_id: UUID,
        limit: int = 10,
        status: str | None = None,
    ) -> list[Conversation]:
        """Get conversations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            status: Optional status filter

        Returns:
            List of conversations ordered by most recent
        """
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )

        if status:
            query = query.where(Conversation.status == status)

        result = await self.db.execute(query)
        return list(result.scalars().all())
