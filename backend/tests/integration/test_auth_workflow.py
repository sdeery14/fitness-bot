"""Integration test for authentication workflow."""
import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.mark.asyncio
async def test_auth_workflow():
    """Test complete authentication workflow: register → login → access protected endpoint."""
    # Use unique email to avoid conflicts
    import uuid
    test_email = f"testauth_{uuid.uuid4().hex[:8]}@example.com"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register a new user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Test User",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "beginner",
            },
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "data" in register_data
        assert "access_token" in register_data["data"]
        assert "refresh_token" in register_data["data"]
        access_token = register_data["data"]["access_token"]

        # 2. Access protected endpoint with token
        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert "data" in me_data
        assert me_data["data"]["email"] == test_email
        assert me_data["data"]["full_name"] == "Test User"

        # 3. Login with credentials
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "data" in login_data
        assert "access_token" in login_data["data"]
        assert "refresh_token" in login_data["data"]

        # 4. Refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_data["data"]["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "data" in refresh_data
        assert "access_token" in refresh_data["data"]


@pytest.mark.asyncio
async def test_invalid_login():
    """Test login with invalid credentials."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
