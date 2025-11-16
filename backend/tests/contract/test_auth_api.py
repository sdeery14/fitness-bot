"""Contract tests for authentication API endpoints.

Tests validate that auth endpoints conform to the API contracts defined in
specs/001-ai-fitness-planner/contracts/api-contracts.md
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class TestRegisterEndpoint:
    """Contract tests for POST /api/v1/auth/register"""

    @pytest.mark.asyncio
    async def test_register_success(self, async_client: AsyncClient):
        """Test successful user registration returns 201 with correct schema."""
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User",
            "date_of_birth": "1990-01-15",
            "current_fitness_level": "beginner"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Contract: 201 Created status
        assert response.status_code == 201

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains user data
        assert "data" in data
        assert "user" in data["data"]
        user_data = data["data"]["user"]
        assert "id" in user_data
        assert user_data["email"] == payload["email"]
        assert user_data["full_name"] == payload["full_name"]
        assert "created_at" in user_data

        # Contract: Response contains access token
        assert "access_token" in data["data"]
        assert "token_type" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "expires_in" in data["data"]

        # Contract: Response contains metadata
        assert "metadata" in data
        assert "timestamp" in data["metadata"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test registration with existing email returns 409 CONFLICT."""
        payload = {
            "email": test_user.email,  # Existing user email
            "password": "SecurePass123!",
            "full_name": "Duplicate User",
            "date_of_birth": "1990-01-15",
            "current_fitness_level": "beginner"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Contract: 409 CONFLICT status
        assert response.status_code == 409

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["code"] == "CONFLICT" or "ALREADY_EXISTS" in data["error"]["code"]

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email returns 400 BAD_REQUEST."""
        payload = {
            "email": "not-an-email",  # Invalid format
            "password": "SecurePass123!",
            "full_name": "Test User",
            "date_of_birth": "1990-01-15",
            "current_fitness_level": "beginner"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Contract: 400 BAD_REQUEST status
        assert response.status_code == 400

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]

    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password returns 400 BAD_REQUEST."""
        payload = {
            "email": "weak@example.com",
            "password": "123",  # Too weak
            "full_name": "Test User",
            "date_of_birth": "1990-01-15",
            "current_fitness_level": "beginner"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Contract: 400 BAD_REQUEST status
        assert response.status_code == 400

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"


class TestLoginEndpoint:
    """Contract tests for POST /api/v1/auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """Test successful login returns 200 with correct schema."""
        payload = {
            "email": test_user.email,
            "password": "testpass123"  # Default test user password
        }

        response = await async_client.post("/api/v1/auth/login", json=payload)

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains tokens
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "token_type" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "expires_in" in data["data"]

        # Contract: Response contains user data
        assert "user" in data["data"]
        user_data = data["data"]["user"]
        assert user_data["id"] == str(test_user.id)
        assert user_data["email"] == test_user.email
        assert user_data["full_name"] == test_user.full_name

        # Contract: Response contains metadata
        assert "metadata" in data
        assert "timestamp" in data["metadata"]

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient, test_user: User):
        """Test login with wrong password returns 401 UNAUTHORIZED."""
        payload = {
            "email": test_user.email,
            "password": "wrong_password"
        }

        response = await async_client.post("/api/v1/auth/login", json=payload)

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]
        assert data["error"]["code"] == "UNAUTHORIZED" or "INVALID_CREDENTIALS" in data["error"]["code"]
        assert "message" in data["error"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent email returns 401 UNAUTHORIZED."""
        payload = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }

        response = await async_client.post("/api/v1/auth/login", json=payload)

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"


class TestRefreshTokenEndpoint:
    """Contract tests for POST /api/v1/auth/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client: AsyncClient, test_user: User):
        """Test successful token refresh returns 200 with new access token."""
        # First login to get refresh token
        login_payload = {
            "email": test_user.email,
            "password": "testpass123"
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        refresh_token = login_response.json()["data"]["refresh_token"]

        # Now refresh
        payload = {"refresh_token": refresh_token}
        response = await async_client.post("/api/v1/auth/refresh", json=payload)

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains new access token
        assert "data" in data
        assert "access_token" in data["data"]
        assert "token_type" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "expires_in" in data["data"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test refresh with invalid token returns 401 UNAUTHORIZED."""
        payload = {"refresh_token": "invalid_token"}

        response = await async_client.post("/api/v1/auth/refresh", json=payload)

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]

