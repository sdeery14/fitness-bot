"""User service for user profile and preference management."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserService:
    """Service for user profile operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize user service.

        Args:
            db: Database session for user queries
        """
        self.db = db

    async def get_user(self, user_id: UUID) -> User | None:
        """Retrieve a user by ID.

        Args:
            user_id: User's UUID

        Returns:
            User instance if found, None otherwise
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by email address.

        Args:
            email: User's email address

        Returns:
            User instance if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(
        self,
        user_id: UUID,
        name: str | None = None,
        email: str | None = None,
    ) -> User | None:
        """Update user profile information.

        Args:
            user_id: User's UUID
            name: Optional new name
            email: Optional new email

        Returns:
            Updated user instance if found, None otherwise
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        if name is not None:
            user.name = name
        if email is not None:
            # Check if email already exists
            existing = await self.get_user_by_email(email)
            if existing and existing.id != user_id:
                raise ValueError("Email already in use")
            user.email = email

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_preferences(
        self,
        user_id: UUID,
        preferences: dict,
    ) -> User | None:
        """Update user preferences.

        Args:
            user_id: User's UUID
            preferences: New preferences dictionary (replaces existing)

        Returns:
            Updated user instance if found, None otherwise
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        user.preferences = preferences
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def merge_preferences(
        self,
        user_id: UUID,
        preferences: dict,
    ) -> User | None:
        """Merge new preferences with existing preferences.

        Args:
            user_id: User's UUID
            preferences: Preferences to merge (existing keys updated, new keys added)

        Returns:
            Updated user instance if found, None otherwise
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        # Merge preferences (new values override existing)
        current_prefs = user.preferences or {}
        updated_prefs = {**current_prefs, **preferences}
        user.preferences = updated_prefs

        await self.db.commit()
        await self.db.refresh(user)
        return user
