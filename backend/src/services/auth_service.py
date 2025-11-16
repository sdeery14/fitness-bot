"""Authentication service for user registration, login, and token management.

Implements secure password hashing with bcrypt and JWT token generation.
"""
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.config import get_settings

settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize auth service.

        Args:
            db: Database session for user queries
        """
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password as string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token.

        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    def create_refresh_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT refresh token.

        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    async def register(
        self,
        email: str,
        password: str,
        name: str,
        date_of_birth: str | None = None,
        fitness_level: str | None = None,
    ) -> User:
        """Register a new user.

        Args:
            email: User email address
            password: Plain text password
            name: User's full name
            date_of_birth: User's date of birth (ISO format YYYY-MM-DD)
            fitness_level: User's fitness level (beginner, intermediate, advanced)

        Returns:
            Created user instance

        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("Email already registered")

        # Parse date_of_birth if provided
        dob_datetime = None
        if date_of_birth:
            from datetime import datetime
            try:
                dob_datetime = datetime.fromisoformat(date_of_birth)
            except ValueError as e:
                raise ValueError("Invalid date_of_birth format. Expected YYYY-MM-DD") from e

        # Create new user
        hashed_password = self.hash_password(password)
        user = User(
            email=email,
            password_hash=hashed_password,
            name=name,
            date_of_birth=dob_datetime,
            fitness_level=fitness_level,
            preferences={},  # Empty preferences initially
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def login(self, email: str, password: str) -> tuple[User, str, str] | None:
        """Authenticate a user and generate tokens.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (user, access_token, refresh_token) if successful, None if failed
        """
        # Fetch user by email
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(password, user.password_hash):
            return None

        # Generate tokens
        access_token = self.create_access_token(data={"sub": str(user.id)})
        refresh_token = self.create_refresh_token(data={"sub": str(user.id)})

        return user, access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str | None:
        """Generate a new access token from a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token if refresh token is valid, None otherwise
        """
        payload = self.verify_token(refresh_token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Verify user still exists
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Generate new access token
        access_token = self.create_access_token(data={"sub": str(user.id)})
        return access_token
