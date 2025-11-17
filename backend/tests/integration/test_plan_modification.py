"""Integration test for AI-assisted plan modification."""
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_workout_intensity_modification():
    """Test modifying workout intensity through AI conversation."""
    # Use unique email to avoid conflicts
    test_email = f"testmodify_{uuid4().hex[:8]}@example.com"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Modify Test User",
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
                "goal_description": "Build muscle and increase strength",
                "duration_weeks": 12,
                "plan_snapshot": {
                    "phases": [
                        {
                            "phase_number": 1,
                            "name": "Foundation",
                            "duration_weeks": 4,
                            "focus": "Building base strength",
                        }
                    ],
                    "workouts": [
                        {
                            "name": "Upper Body Strength",
                            "type": "strength",
                            "exercises": [
                                {"name": "Bench Press", "sets": 3, "reps": 10, "weight_kg": 60},
                                {"name": "Rows", "sets": 3, "reps": 10, "weight_kg": 50},
                            ],
                        }
                    ],
                    "meals": [],
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

        # 4. Request workout intensity increase
        message_response = await client.post(
            f"/api/v1/ai/conversations/{conversation_id}/messages",
            headers=headers,
            json={
                "message": "I want to increase my workout intensity by 10%. "
                          f"My fitness plan ID is {fitness_plan_id}. "
                          "Please adjust my workouts accordingly.",
            },
        )
        assert message_response.status_code == 200
        message_data = message_response.json()["data"]
        
        # 5. Verify AI responded with modification details
        assert "assistant_response" in message_data
        ai_response = message_data["assistant_response"]
        assert ai_response is not None
        assert len(ai_response) > 0


@pytest.mark.asyncio
async def test_meal_macro_adjustment():
    """Test adjusting meal macros through AI conversation."""
    test_email = f"testmacros_{uuid4().hex[:8]}@example.com"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Macros Test User",
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
                "goal_description": "Lose weight with high protein diet",
                "duration_weeks": 8,
                "plan_snapshot": {
                    "phases": [],
                    "workouts": [],
                    "meals": [
                        {
                            "name": "Breakfast",
                            "time": "08:00",
                            "items": [
                                {
                                    "name": "Oatmeal with berries",
                                    "quantity": "1 cup",
                                    "calories": 300,
                                    "protein_g": 10,
                                    "carbs_g": 54,
                                    "fat_g": 6,
                                }
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

        # 4. Request higher protein meals
        message_response = await client.post(
            f"/api/v1/ai/conversations/{conversation_id}/messages",
            headers=headers,
            json={
                "message": "I want to increase protein in my meals. "
                          f"My fitness plan ID is {fitness_plan_id}. "
                          "Can you suggest higher protein alternatives?",
            },
        )
        assert message_response.status_code == 200
        message_data = message_response.json()["data"]
        
        # 5. Verify AI responded
        assert "assistant_response" in message_data
        ai_response = message_data["assistant_response"]
        assert ai_response is not None
        assert "protein" in ai_response.lower()


@pytest.mark.asyncio
async def test_workout_alternatives_request():
    """Test requesting exercise alternatives through AI conversation."""
    test_email = f"testalts_{uuid4().hex[:8]}@example.com"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register and authenticate user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Alternatives Test User",
                "date_of_birth": "1990-01-01",
                "current_fitness_level": "beginner",
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
                "goal_type": "general_fitness",
                "goal_description": "Get fit at home",
                "duration_weeks": 8,
                "plan_snapshot": {
                    "phases": [],
                    "workouts": [
                        {
                            "name": "Full Body Workout",
                            "type": "strength",
                            "exercises": [
                                {"name": "Squats", "sets": 3, "reps": 12},
                                {"name": "Push-ups", "sets": 3, "reps": 10},
                            ],
                        }
                    ],
                    "meals": [],
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

        # 4. Request exercise alternatives due to injury
        message_response = await client.post(
            f"/api/v1/ai/conversations/{conversation_id}/messages",
            headers=headers,
            json={
                "message": "I have a knee injury and can't do squats. "
                          f"My fitness plan ID is {fitness_plan_id}. "
                          "Can you suggest alternative exercises?",
            },
        )
        assert message_response.status_code == 200
        message_data = message_response.json()["data"]
        
        # 5. Verify AI responded with alternatives
        assert "assistant_response" in message_data
        ai_response = message_data["assistant_response"]
        assert ai_response is not None
        assert len(ai_response) > 0

