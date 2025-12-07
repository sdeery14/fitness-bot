"""User profile endpoints."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.api.deps import CurrentUserId, DatabaseSession
from src.schemas import create_success_response
from src.services.user_service import UserService

router = APIRouter()


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    name: str
    preferences: dict

    class Config:
        """Pydantic config."""

        from_attributes = True


class UpdateUserRequest(BaseModel):
    """User profile update request."""

    name: str | None = None
    email: EmailStr | None = None
    preferences: dict | None = None
    timezone: str | None = None  # IANA timezone (e.g., "America/New_York")


@router.get("/me")
async def get_current_user(
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get current user profile.

    Args:
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        User profile data

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

    return create_success_response({
        "id": str(user.id),
        "email": user.email,
        "full_name": user.name or "",
        "preferences": user.preferences or {},
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


@router.patch("/me")
async def update_current_user(
    request: UpdateUserRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Update current user profile.

    Args:
        request: Update data (name, email, preferences)
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: If user not found or email already in use
    """
    user_service = UserService(db)

    try:
        # Update profile fields
        if request.name is not None or request.email is not None or request.timezone is not None:
            user = await user_service.update_user(
                user_id=user_id,
                name=request.name,
                email=request.email,
                timezone=request.timezone,
            )
        else:
            user = await user_service.get_user(user_id)

        # Update preferences separately if provided
        if request.preferences is not None and user:
            user = await user_service.merge_preferences(
                user_id=user_id,
                preferences=request.preferences,
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return create_success_response({
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name or "",
            "preferences": user.preferences or {},
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        })

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
