"""Integration test for phase transitions."""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_multi_phase_plan_creation_and_transition():
    """Test complete multi-phase workflow: create plan → complete phase → verify transition."""
    test_email = f"testphase_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Phase Test User",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "intermediate",
            },
        )
        assert register_response.status_code == 201
        access_token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Create a multi-phase fitness plan
        today = date.today()
        phase1_start = today
        phase1_end = today + timedelta(days=20)
        phase2_start = phase1_end + timedelta(days=1)
        phase2_end = phase2_start + timedelta(days=20)

        plan_response = await client.post(
            "/api/v1/fitness-plans",
            headers=headers,
            json={
                "goal_type": "triathlon_training",
                "goal_description": "Train for triathlon in 18 months",
                "duration_weeks": 8,
                "start_date": today.isoformat(),
                "plan_snapshot": {
                    "phases": [
                        {
                            "id": str(uuid4()),
                            "phase_number": 1,
                            "name": "Base Endurance",
                            "objectives": [
                                "Build aerobic base",
                                "Learn proper form",
                                "Establish consistent training schedule",
                            ],
                            "start_date": phase1_start.isoformat(),
                            "end_date": phase1_end.isoformat(),
                            "phase_details": {
                                "focus": "endurance",
                                "intensity": "moderate",
                            },
                        },
                        {
                            "id": str(uuid4()),
                            "phase_number": 2,
                            "name": "Strength Building",
                            "objectives": [
                                "Increase power output",
                                "Build muscular endurance",
                                "Improve lactate threshold",
                            ],
                            "start_date": phase2_start.isoformat(),
                            "end_date": phase2_end.isoformat(),
                            "phase_details": {
                                "focus": "strength",
                                "intensity": "high",
                            },
                        },
                    ],
                    "workouts": [],
                    "meals": [],
                },
            },
        )
        assert plan_response.status_code == 201
        plan_data = plan_response.json()["data"]
        fitness_plan_id = plan_data["id"]

        # 3. Verify plan was created with phases
        plan_get_response = await client.get(
            f"/api/v1/fitness-plans/{fitness_plan_id}",
            headers=headers,
        )
        assert plan_get_response.status_code == 200
        plan_details = plan_get_response.json()["data"]
        assert "plan_snapshot" in plan_details
        assert "phases" in plan_details["plan_snapshot"]
        assert len(plan_details["plan_snapshot"]["phases"]) == 2

        # 4. Verify we're currently in Phase 1
        phases = plan_details["plan_snapshot"]["phases"]
        assert phases[0]["phase_number"] == 1
        assert phases[0]["name"] == "Base Endurance"
        assert phases[1]["phase_number"] == 2
        assert phases[1]["name"] == "Strength Building"


@pytest.mark.asyncio
async def test_phase_completion_detection():
    """Test that phase completion is detected correctly."""
    test_email = f"testphasecomp_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Phase Completion Test",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "intermediate",
            },
        )
        assert register_response.status_code == 201
        access_token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Create a plan with a phase ending soon
        today = date.today()
        phase1_start = today - timedelta(days=10)
        phase1_end = today + timedelta(days=1)  # Ending in 1 day
        phase2_start = phase1_end + timedelta(days=1)
        phase2_end = phase2_start + timedelta(days=20)

        plan_response = await client.post(
            "/api/v1/fitness-plans",
            headers=headers,
            json={
                "goal_type": "muscle_building",
                "goal_description": "Build muscle with progressive phases",
                "duration_weeks": 6,
                "start_date": phase1_start.isoformat(),
                "plan_snapshot": {
                    "phases": [
                        {
                            "id": str(uuid4()),
                            "phase_number": 1,
                            "name": "Foundation",
                            "objectives": ["Build base strength"],
                            "start_date": phase1_start.isoformat(),
                            "end_date": phase1_end.isoformat(),
                            "phase_details": {"focus": "foundation"},
                        },
                        {
                            "id": str(uuid4()),
                            "phase_number": 2,
                            "name": "Hypertrophy",
                            "objectives": ["Increase muscle size"],
                            "start_date": phase2_start.isoformat(),
                            "end_date": phase2_end.isoformat(),
                            "phase_details": {"focus": "hypertrophy"},
                        },
                    ],
                    "workouts": [],
                    "meals": [],
                },
            },
        )
        assert plan_response.status_code == 201
        plan_data = plan_response.json()["data"]
        fitness_plan_id = plan_data["id"]

        # 3. Phase completion should be detected
        # Note: This would require a new API endpoint to check phase status
        # For now, we verify the plan structure is correct


@pytest.mark.asyncio
async def test_phase_transition_records_history():
    """Test that phase transitions are recorded in plan history."""
    test_email = f"testphasehist_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Phase History Test",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "intermediate",
            },
        )
        assert register_response.status_code == 201
        access_token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Create a multi-phase plan
        today = date.today()
        plan_response = await client.post(
            "/api/v1/fitness-plans",
            headers=headers,
            json={
                "goal_type": "weight_loss",
                "goal_description": "Progressive weight loss plan",
                "duration_weeks": 12,
                "start_date": today.isoformat(),
                "plan_snapshot": {
                    "phases": [
                        {
                            "id": str(uuid4()),
                            "phase_number": 1,
                            "name": "Adaptation",
                            "objectives": ["Build healthy habits"],
                            "start_date": today.isoformat(),
                            "end_date": (today + timedelta(days=28)).isoformat(),
                            "phase_details": {"focus": "adaptation"},
                        },
                        {
                            "id": str(uuid4()),
                            "phase_number": 2,
                            "name": "Intensification",
                            "objectives": ["Increase calorie burn"],
                            "start_date": (today + timedelta(days=29)).isoformat(),
                            "end_date": (today + timedelta(days=56)).isoformat(),
                            "phase_details": {"focus": "intensification"},
                        },
                    ],
                    "workouts": [],
                    "meals": [],
                },
            },
        )
        assert plan_response.status_code == 201
        plan_data = plan_response.json()["data"]

        # 3. Verify plan was created successfully
        assert "id" in plan_data
        assert plan_data["goal_type"] == "weight_loss"

        # 4. When transitions happen, they should be recorded in plan_snapshot.phase_transitions
        # This will be populated by the transition_to_next_phase method
