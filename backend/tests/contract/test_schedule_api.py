"""Contract tests for schedule API endpoints.

Tests validate that schedule endpoints conform to the API contracts defined in
specs/001-ai-fitness-planner/contracts/api-contracts.md
"""
import pytest
from httpx import AsyncClient


class TestTodayScheduleEndpoint:
    """Contract tests for GET /api/v1/schedules/today"""

    @pytest.mark.asyncio
    async def test_get_today_schedule_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting today's schedule returns correct schema."""
        response = await async_client.get(
            "/api/v1/schedules/today",
            headers=auth_headers,
        )

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response contains required fields
        assert "date" in data
        assert "entries" in data
        assert isinstance(data["entries"], list)
        assert "summary" in data
        assert "total_workouts" in data["summary"]
        assert "total_meals" in data["summary"]

    @pytest.mark.asyncio
    async def test_get_today_schedule_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test accessing today's schedule without auth returns 401."""
        response = await async_client.get("/api/v1/schedules/today")
        assert response.status_code == 401


class TestUpcomingScheduleEndpoint:
    """Contract tests for GET /api/v1/schedules/upcoming"""

    @pytest.mark.asyncio
    async def test_get_upcoming_schedule_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting upcoming schedule returns correct schema."""
        response = await async_client.get(
            "/api/v1/schedules/upcoming?days=14",
            headers=auth_headers,
        )

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response contains required fields
        assert "start_date" in data
        assert "end_date" in data
        assert "entries" in data
        assert isinstance(data["entries"], list)
        assert "grouped_by_date" in data
        assert isinstance(data["grouped_by_date"], dict)


class TestCompleteEntryEndpoint:
    """Contract tests for POST /api/v1/schedules/entries/{id}/complete"""

    @pytest.mark.asyncio
    async def test_complete_entry_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test completing non-existent entry returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())

        response = await async_client.post(
            f"/api/v1/schedules/entries/{fake_id}/complete",
            json={},
            headers=auth_headers,
        )

        # Contract: 404 Not Found for non-existent entry
        assert response.status_code == 404


class TestSkipEntryEndpoint:
    """Contract tests for POST /api/v1/schedules/entries/{id}/skip"""

    @pytest.mark.asyncio
    async def test_skip_entry_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test skipping entry without auth returns 401."""
        import uuid
        fake_id = str(uuid.uuid4())

        response = await async_client.post(
            f"/api/v1/schedules/entries/{fake_id}/skip",
            json={"reason": "Test"},
        )

        assert response.status_code == 401
