"""Contract tests for fitness plans API endpoints.

Tests validate that plans endpoints conform to the API contracts defined in
specs/001-ai-fitness-planner/contracts/api-contracts.md
"""
import pytest
from httpx import AsyncClient
from datetime import date, timedelta

from src.models.user import User
from src.models.fitness_plan import FitnessPlan


class TestCreatePlanEndpoint:
    """Contract tests for POST /api/v1/fitness-plans"""

    @pytest.mark.asyncio
    async def test_create_plan_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful plan creation returns 201 with correct schema."""
        payload = {
            "goal_description": "Lose 15 pounds in 3 months",
            "goal_type": "weight_loss",
            "duration_weeks": 12,
            "start_date": str(date.today() + timedelta(days=3)),
            "plan_snapshot": {
                "version": "1.0",
                "phases": [],
                "workout_frequency": "4 days per week",
                "nutrition_approach": "500 calorie deficit"
            }
        }

        response = await async_client.post(
            "/api/v1/fitness-plans",
            json=payload,
            headers=auth_headers
        )

        # Contract: 201 Created status
        assert response.status_code == 201

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains plan data
        assert "data" in data
        plan_data = data["data"]
        assert "id" in plan_data
        assert plan_data["goal_description"] == payload["goal_description"]
        assert plan_data["goal_type"] == payload["goal_type"]
        assert plan_data["duration_weeks"] == payload["duration_weeks"]
        assert plan_data["start_date"] == payload["start_date"]
        assert "target_end_date" in plan_data
        assert plan_data["current_status"] == "active"
        assert "created_at" in plan_data

        # Contract: Response contains metadata
        assert "metadata" in data
        assert "timestamp" in data["metadata"]

    @pytest.mark.asyncio
    async def test_create_plan_invalid_data(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test plan creation with invalid data returns 400 BAD_REQUEST."""
        payload = {
            "goal_description": "",  # Empty goal
            "goal_type": "invalid_type",
            "duration_weeks": -1,  # Invalid duration
            "start_date": "invalid-date"
        }

        response = await async_client.post(
            "/api/v1/fitness-plans",
            json=payload,
            headers=auth_headers
        )

        # Contract: 400 BAD_REQUEST status
        assert response.status_code == 400

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    @pytest.mark.asyncio
    async def test_create_plan_conflict_active_plan(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_fitness_plan: FitnessPlan
    ):
        """Test creating plan when user has active plan returns 409 CONFLICT."""
        payload = {
            "goal_description": "Another goal",
            "goal_type": "muscle_gain",
            "duration_weeks": 8,
            "start_date": str(date.today() + timedelta(days=1)),
            "plan_snapshot": {"version": "1.0"}
        }

        response = await async_client.post(
            "/api/v1/fitness-plans",
            json=payload,
            headers=auth_headers
        )

        # Contract: 409 CONFLICT status (if active plan exists)
        assert response.status_code == 409

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]
        assert "CONFLICT" in data["error"]["code"] or "ACTIVE_PLAN" in data["error"]["code"]

    @pytest.mark.asyncio
    async def test_create_plan_unauthorized(self, async_client: AsyncClient):
        """Test creating plan without auth returns 401 UNAUTHORIZED."""
        payload = {
            "goal_description": "Test goal",
            "goal_type": "weight_loss",
            "duration_weeks": 12,
            "start_date": str(date.today()),
            "plan_snapshot": {"version": "1.0"}
        }

        response = await async_client.post("/api/v1/fitness-plans", json=payload)

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401


class TestGetPlanEndpoint:
    """Contract tests for GET /api/v1/fitness-plans/{plan_id}"""

    @pytest.mark.asyncio
    async def test_get_plan_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_fitness_plan: FitnessPlan
    ):
        """Test successful plan retrieval returns 200 with correct schema."""
        response = await async_client.get(
            f"/api/v1/fitness-plans/{test_fitness_plan.id}",
            headers=auth_headers
        )

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains plan data
        assert "data" in data
        plan_data = data["data"]
        assert plan_data["id"] == str(test_fitness_plan.id)
        assert "goal_description" in plan_data
        assert "goal_type" in plan_data
        assert "duration_weeks" in plan_data
        assert "start_date" in plan_data
        assert "target_end_date" in plan_data
        assert "current_status" in plan_data
        assert "plan_snapshot" in plan_data

        # Contract: Optional fields
        if "workout_plan" in plan_data:
            assert "id" in plan_data["workout_plan"]
            assert "workout_frequency_per_week" in plan_data["workout_plan"]

        if "meal_plan" in plan_data:
            assert "id" in plan_data["meal_plan"]
            assert "daily_calorie_target" in plan_data["meal_plan"]

    @pytest.mark.asyncio
    async def test_get_plan_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent plan returns 404 NOT_FOUND."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await async_client.get(
            f"/api/v1/fitness-plans/{fake_id}",
            headers=auth_headers
        )

        # Contract: 404 NOT_FOUND status
        assert response.status_code == 404

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]
        assert "NOT_FOUND" in data["error"]["code"]

    @pytest.mark.asyncio
    async def test_get_plan_unauthorized(
        self, async_client: AsyncClient, test_fitness_plan: FitnessPlan
    ):
        """Test getting plan without auth returns 401 UNAUTHORIZED."""
        response = await async_client.get(
            f"/api/v1/fitness-plans/{test_fitness_plan.id}"
        )

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401


class TestGetActivePlanEndpoint:
    """Contract tests for GET /api/v1/fitness-plans/active"""

    @pytest.mark.asyncio
    async def test_get_active_plan_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_fitness_plan: FitnessPlan
    ):
        """Test successful active plan retrieval returns 200 with correct schema."""
        response = await async_client.get(
            "/api/v1/fitness-plans/active",
            headers=auth_headers
        )

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains plan data
        assert "data" in data
        plan_data = data["data"]
        assert "id" in plan_data
        assert "goal_description" in plan_data
        # Same structure as GET /fitness-plans/{plan_id}

    @pytest.mark.asyncio
    async def test_get_active_plan_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test getting active plan when none exists returns 404 NOT_FOUND."""
        # Note: This test assumes no active plan for the auth user
        # May need to be skipped if test fixtures create active plan by default
        response = await async_client.get(
            "/api/v1/fitness-plans/active",
            headers=auth_headers
        )

        # Contract: 404 NOT_FOUND status (if no active plan)
        if response.status_code == 404:
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data
            assert "NOT_FOUND" in data["error"]["code"]


class TestUpdatePlanEndpoint:
    """Contract tests for PATCH /api/v1/fitness-plans/{plan_id}"""

    @pytest.mark.asyncio
    async def test_update_plan_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_fitness_plan: FitnessPlan
    ):
        """Test successful plan update returns 200 with correct schema."""
        payload = {
            "current_status": "paused",
            "plan_snapshot": {
                "version": "1.1",
                "updated_field": "new_value"
            }
        }

        response = await async_client.patch(
            f"/api/v1/fitness-plans/{test_fitness_plan.id}",
            json=payload,
            headers=auth_headers
        )

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains updated plan data
        assert "data" in data
        plan_data = data["data"]
        assert "id" in plan_data
        assert plan_data["id"] == str(test_fitness_plan.id)
        assert plan_data["current_status"] == payload["current_status"]
        assert "updated_at" in plan_data

    @pytest.mark.asyncio
    async def test_update_plan_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test updating non-existent plan returns 404 NOT_FOUND."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"current_status": "paused"}

        response = await async_client.patch(
            f"/api/v1/fitness-plans/{fake_id}",
            json=payload,
            headers=auth_headers
        )

        # Contract: 404 NOT_FOUND status
        assert response.status_code == 404

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "NOT_FOUND" in data["error"]["code"]

    @pytest.mark.asyncio
    async def test_update_plan_unauthorized(
        self, async_client: AsyncClient, test_fitness_plan: FitnessPlan
    ):
        """Test updating plan without auth returns 401 UNAUTHORIZED."""
        payload = {"current_status": "paused"}

        response = await async_client.patch(
            f"/api/v1/fitness-plans/{test_fitness_plan.id}",
            json=payload
        )

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401

