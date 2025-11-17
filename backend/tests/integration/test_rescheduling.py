"""Integration test for disruption handling and schedule rescheduling."""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_disruption_rescheduling_workflow():
    """Test complete disruption handling workflow: create plan → report disruption → verify schedule adjustment."""
    # Use unique email to avoid conflicts
    test_email = f"testdisrupt_{uuid4().hex[:8]}@example.com"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Disruption Test User",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "intermediate",
            },
        )
        assert register_response.status_code == 201
        access_token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Create a fitness plan
        plan_response = await client.post(
            "/api/v1/fitness-plans",
            headers=headers,
            json={
                "goal_type": "weight_loss",
                "goal_description": "Lose 10 pounds in 8 weeks",
                "target_weight_kg": "70",
                "duration_weeks": 8,
                "plan_snapshot": {
                    "phases": [],
                    "workouts": [],
                    "meals": [],
                },
            },
        )
        assert plan_response.status_code == 201
        plan_data = plan_response.json()["data"]
        fitness_plan_id = plan_data["id"]

        # 3. Create a schedule for the plan
        schedule_response = await client.post(
            "/api/v1/schedules",
            headers=headers,
            json={
                "fitness_plan_id": fitness_plan_id,
                "start_date": date.today().isoformat(),
            },
        )
        assert schedule_response.status_code == 201
        schedule_data = schedule_response.json()["data"]
        schedule_id = schedule_data["id"]

        # 4. Report a moderate disruption (illness for 5 days)
        disruption_start = date.today()
        disruption_end = date.today() + timedelta(days=4)  # 5 days total

        reschedule_response = await client.post(
            "/api/v1/ai/reschedule",
            headers=headers,
            json={
                "fitness_plan_id": fitness_plan_id,
                "disruption_type": "illness",
                "severity": "moderate",
                "start_date": disruption_start.isoformat(),
                "end_date": disruption_end.isoformat(),
                "description": "Got the flu, unable to work out for a week. Need to reschedule my workouts.",
            },
        )
        assert reschedule_response.status_code == 200
        reschedule_data = reschedule_response.json()["data"]

        # 6. Verify rescheduling results
        assert "disruption_id" in reschedule_data
        assert "resolution_strategy" in reschedule_data
        assert reschedule_data["resolution_strategy"] in ["reschedule", "extend_timeline", "skip", "reassess"]
        assert "workouts_affected" in reschedule_data
        assert "meals_affected" in reschedule_data
        assert "ai_message" in reschedule_data

        # 7. Verify timeline extension if applied
        if reschedule_data["timeline_extension_days"] > 0:
            assert reschedule_data["new_end_date"] is not None

        # 8. Verify schedule entries were updated
        updated_entries_response = await client.get(
            f"/api/v1/schedules/{schedule_id}/entries",
            headers=headers,
            params={
                "start_date": disruption_start.isoformat(),
                "end_date": disruption_end.isoformat(),
            },
        )
        assert updated_entries_response.status_code == 200
        disruption_period_entries = updated_entries_response.json()["data"]

        # Verify entries during disruption period are rescheduled or skipped
        for entry in disruption_period_entries:
            assert entry["completion_status"] in ["rescheduled", "skipped", "completed"]


@pytest.mark.asyncio
async def test_disruption_without_end_date():
    """Test disruption reporting with ongoing disruption (no end date)."""
    test_email = f"testdisrupt2_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and get token
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Ongoing Disruption Test",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "beginner",
            },
        )
        access_token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Create plan
        plan_response = await client.post(
            "/api/v1/fitness-plans",
            headers=headers,
            json={
                "goal_type": "muscle_gain",
                "goal_description": "Build strength",
                "duration_weeks": 12,
                "plan_snapshot": {"phases": [], "workouts": [], "meals": []},
            },
        )
        fitness_plan_id = plan_response.json()["data"]["id"]

        # 3. Report ongoing disruption (no end_date)
        reschedule_response = await client.post(
            "/api/v1/ai/reschedule",
            headers=headers,
            json={
                "fitness_plan_id": fitness_plan_id,
                "disruption_type": "injury",
                "severity": "severe",
                "start_date": date.today().isoformat(),
                "end_date": None,  # Ongoing
                "description": "Injured my back, unsure when I can resume training.",
            },
        )
        assert reschedule_response.status_code == 200
        result = reschedule_response.json()["data"]

        # Should handle ongoing disruption appropriately
        assert result["resolution_strategy"] in ["reassess", "extend_timeline"]
        assert "ai_message" in result


@pytest.mark.asyncio
async def test_invalid_disruption_report():
    """Test disruption reporting with invalid data."""
    test_email = f"testdisrupt3_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Invalid Test",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "beginner",
            },
        )
        access_token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Try to report disruption for non-existent plan
        fake_plan_id = str(uuid4())
        response = await client.post(
            "/api/v1/ai/reschedule",
            headers=headers,
            json={
                "fitness_plan_id": fake_plan_id,
                "disruption_type": "illness",
                "severity": "minor",
                "start_date": date.today().isoformat(),
                "description": "Test disruption",
            },
        )
        assert response.status_code == 404  # Plan not found

        # 3. Try with invalid disruption type
        plan_response = await client.post(
            "/api/v1/fitness-plans",
            headers=headers,
            json={
                "goal_type": "weight_loss",
                "goal_description": "Test",
                "duration_weeks": 4,
                "plan_snapshot": {},
            },
        )
        valid_plan_id = plan_response.json()["data"]["id"]

        invalid_response = await client.post(
            "/api/v1/ai/reschedule",
            headers=headers,
            json={
                "fitness_plan_id": valid_plan_id,
                "disruption_type": "invalid_type",  # Invalid
                "severity": "minor",
                "start_date": date.today().isoformat(),
                "description": "Test disruption",
            },
        )
        assert invalid_response.status_code == 422  # Validation error

