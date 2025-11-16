"""API dependencies for dependency injection."""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.middleware.auth_middleware import verify_jwt_token

# Database session dependency
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


class HTTPBearerCustom(HTTPBearer):
    """Custom HTTPBearer that returns 401 instead of 403 when no credentials provided."""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """Override to return 401 for missing auth."""
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == 403:
                # Convert 403 to 401 for missing credentials
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from e
            raise


security = HTTPBearerCustom()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Extract current user ID from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User UUID

    Raises:
        HTTPException: If token is invalid or missing user ID
    """
    payload = await verify_jwt_token(credentials)

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: malformed user ID",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    return user_id


# Type alias for current user dependency
CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
