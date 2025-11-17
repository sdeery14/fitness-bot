"""User service for user profile and preference management."""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.progress import ProgressRecord
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

    async def check_inactivity(
        self,
        user_id: UUID,
        fitness_plan_id: UUID,
        inactivity_threshold_days: int = 14,
    ) -> dict:
        """Check for extended inactivity periods in user's fitness plan progress (FR-018).

        Detects gaps of 14+ days (configurable) with no progress records,
        which may indicate the user has abandoned their plan or needs reassessment.

        Args:
            user_id: User's UUID
            fitness_plan_id: FitnessPlan's UUID
            inactivity_threshold_days: Days of no activity to trigger alert (default 14)

        Returns:
            Dictionary with inactivity analysis:
            {
                'is_inactive': bool,
                'days_since_last_activity': int,
                'last_activity_date': date or None,
                'recommendation': str ('continue', 'check_in', 'reassess')
            }
        """
        # Get the most recent progress record for this plan
        stmt = (
            select(ProgressRecord)
            .where(
                ProgressRecord.user_id == user_id,
                ProgressRecord.fitness_plan_id == fitness_plan_id,
            )
            .order_by(desc(ProgressRecord.record_date))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_record = result.scalar_one_or_none()

        if not last_record:
            # No progress records at all - plan might be brand new
            return {
                "is_inactive": False,
                "days_since_last_activity": 0,
                "last_activity_date": None,
                "recommendation": "continue",
                "message": "No progress records found - plan may be newly created",
            }

        # Calculate days since last activity
        today = datetime.now(UTC).date()
        days_since_activity = (today - last_record.record_date).days

        # Determine inactivity status and recommendation
        is_inactive = days_since_activity >= inactivity_threshold_days
        
        if days_since_activity < 7:
            recommendation = "continue"
            message = "User is actively following the plan"
        elif days_since_activity < inactivity_threshold_days:
            recommendation = "check_in"
            message = f"User has been inactive for {days_since_activity} days - consider sending a reminder"
        else:
            recommendation = "reassess"
            message = f"User has been inactive for {days_since_activity} days - may need plan reassessment or disruption handling"

        return {
            "is_inactive": is_inactive,
            "days_since_last_activity": days_since_activity,
            "last_activity_date": last_record.record_date,
            "recommendation": recommendation,
            "message": message,
        }
