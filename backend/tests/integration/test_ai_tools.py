"""Integration test for AI tools (workout, meal, progress analysis)."""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_workout_alternatives_endpoint():
    """Test GET /workouts/{workout_id}/alternatives endpoint."""
    test_email = f"testworkout_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Workout Test User",
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
                "goal_type": "muscle_building",
                "goal_description": "Build muscle",
                "duration_weeks": 12,
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

        # 3. Create a workout plan using plan service
        # We'll need to add a workout through the database
        # For now, we'll test that the endpoint exists and handles not found correctly
        workout_id = uuid4()
        alternatives_response = await client.get(
            f"/api/v1/workouts/{workout_id}/alternatives",
            headers=headers,
        )
        # Should return 404 for non-existent workout
        assert alternatives_response.status_code == 404


@pytest.mark.asyncio
async def test_plan_suggestions_endpoint():
    """Test GET /fitness-plans/{plan_id}/suggestions endpoint."""
    test_email = f"testsuggestions_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Suggestions Test User",
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
                "goal_description": "Lose weight sustainably",
                "duration_weeks": 12,
                "start_date": (date.today() - timedelta(days=20)).isoformat(),
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

        # 3. Get suggestions for the plan
        suggestions_response = await client.get(
            f"/api/v1/fitness-plans/{fitness_plan_id}/suggestions",
            headers=headers,
        )
        assert suggestions_response.status_code == 200
        suggestions_data = suggestions_response.json()["data"]

        # 4. Verify suggestions structure
        assert "user_id" in suggestions_data
        assert "fitness_plan_id" in suggestions_data
        assert "analysis_summary" in suggestions_data
        assert "recommendations" in suggestions_data
        assert "generated_at" in suggestions_data

        # 5. Verify analysis summary structure
        analysis = suggestions_data["analysis_summary"]
        assert "overall_adherence" in analysis
        assert "workout_adherence" in analysis
        assert "meal_adherence" in analysis

        # 6. Verify recommendations is a list
        recommendations = suggestions_data["recommendations"]
        assert isinstance(recommendations, list)


@pytest.mark.asyncio
async def test_ai_tools_in_conversation():
    """Test that AI tools are accessible through conversation."""
    test_email = f"testtools_{uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Tools Test User",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "intermediate",
            },
        )
        assert register_response.status_code == 201
        access_token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Create a fitness plan with workouts
        plan_response = await client.post(
            "/api/v1/fitness-plans",
            headers=headers,
            json={
                "goal_type": "muscle_building",
                "goal_description": "Build muscle and strength",
                "duration_weeks": 12,
                "plan_snapshot": {
                    "phases": [],
                    "workouts": [
                        {
                            "name": "Push Day",
                            "type": "strength",
                            "exercises": [
                                {"name": "Bench Press", "sets": 3, "reps": 10},
                            ],
                        }
                    ],
                    "meals": [
                        {
                            "name": "Breakfast",
                            "time": "08:00",
                            "items": [
                                {"name": "Eggs and Toast", "calories": 400},
                            ],
                        }
                    ],
                },
            },
        )
        assert plan_response.status_code == 201
        plan_data = plan_response.json()["data"]
        fitness_plan_id = plan_data["id"]

        # 3. Start a plan_modification conversation
        conversation_response = await client.post(
            "/api/v1/ai/conversations",
            headers=headers,
            json={
                "conversation_type": "plan_modification",
            },
        )
        assert conversation_response.status_code == 200
        conversation_data = conversation_response.json()["data"]
        conversation_id = conversation_data["conversation_id"]

        # 4. Test workout modification tool (intensity increase)
        intensity_message_response = await client.post(
            f"/api/v1/ai/conversations/{conversation_id}/messages",
            headers=headers,
            json={
                "message": f"Increase workout intensity by 15% for plan {fitness_plan_id}",
            },
        )
        assert intensity_message_response.status_code == 200
        intensity_data = intensity_message_response.json()["data"]
        assert "assistant_response" in intensity_data

        # 5. Test meal modification tool (macro adjustment)
        meal_message_response = await client.post(
            f"/api/v1/ai/conversations/{conversation_id}/messages",
            headers=headers,
            json={
                "message": f"Suggest higher protein meal variations for plan {fitness_plan_id}",
            },
        )
        assert meal_message_response.status_code == 200
        meal_data = meal_message_response.json()["data"]
        assert "assistant_response" in meal_data

        # 6. Test progress analysis tool
        progress_message_response = await client.post(
            f"/api/v1/ai/conversations/{conversation_id}/messages",
            headers=headers,
            json={
                "message": f"Analyze my adherence patterns for plan {fitness_plan_id}",
            },
        )
        assert progress_message_response.status_code == 200
        progress_data = progress_message_response.json()["data"]
        assert "assistant_response" in progress_data

