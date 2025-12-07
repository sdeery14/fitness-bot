"""Authentication endpoints."""
import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from src.api.deps import DatabaseSession
from src.schemas import create_error_response, create_success_response
from src.services.auth_service import AuthService

router = APIRouter()


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str
    full_name: str
    date_of_birth: str
    current_fitness_level: str | None = None
    timezone: str | None = None  # IANA timezone (e.g., "America/New_York")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str
    timezone: str | None = None  # Optional: update timezone on login


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: DatabaseSession,
):
    """Register a new user account.

    Args:
        request: Registration details (email, password, full_name, date_of_birth, current_fitness_level)
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If email already registered
    """
    auth_service = AuthService(db)

    try:
        user = await auth_service.register(
            email=request.email,
            password=request.password,
            name=request.full_name,
            date_of_birth=request.date_of_birth,
            fitness_level=request.current_fitness_level or None,
            timezone=request.timezone or "UTC",
        )
    except ValueError as e:
        # Check if it's a duplicate email error
        if "already registered" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=create_error_response(
                    code="ALREADY_EXISTS",
                    message=str(e),
                ),
            ) from e
        # Other validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                code="VALIDATION_ERROR",
                message=str(e),
            ),
        ) from e

    # Generate tokens
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token(data={"sub": str(user.id)})

    from src.config import settings
    return create_success_response({
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name or request.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    })


@router.post("/login")
async def login(
    request: LoginRequest,
    db: DatabaseSession,
):
    """Authenticate user and return tokens.

    Args:
        request: Login credentials (email, password)
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)

    result = await auth_service.login(
        email=request.email,
        password=request.password,
        timezone=request.timezone,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password",
            ),
        )

    user, access_token, refresh_token = result

    from src.config import settings
    return create_success_response({
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name or "",
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    })


@router.post("/refresh")
async def refresh(
    request: RefreshRequest,
    db: DatabaseSession,
):
    """Refresh access token using refresh token.

    Args:
        request: Refresh token
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    auth_service = AuthService(db)

    access_token = await auth_service.refresh_access_token(request.refresh_token)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                code="INVALID_TOKEN",
                message="Invalid or expired refresh token",
            ),
        )

    from src.config import settings
    return create_success_response({
        "access_token": access_token,
        "refresh_token": request.refresh_token,  # Return same refresh token
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    })
