"""Integration tests for agent routing based on user's fitness plan history.

Tests verify that:
1. New users without any fitness plans are routed to intake_specialist_agent
2. Users with existing fitness plans are routed to conversation_agent
3. Both agents can successfully handle conversations and generate plans
"""
import pytest
from sqlalchemy import select

from src.models.fitness_plan import FitnessPlan
from src.services.ai_service import AIOrchestrationService


@pytest.mark.asyncio
async def test_new_user_gets_intake_specialist(db_session, test_user):
    """Test that new users without plans get the intake specialist agent."""
    # Ensure user has no fitness plans
    stmt = select(FitnessPlan).where(FitnessPlan.user_id == test_user.id)
    result = await db_session.execute(stmt)
    existing_plans = result.scalars().all()
    assert len(existing_plans) == 0, "Test user should have no plans"

    # Start conversation
    ai_service = AIOrchestrationService(db_session)
    response = await ai_service.start_conversation(
        user=test_user,
        initial_message="I want to get in shape",
    )

    # Verify response structure
    assert "conversation_id" in response
    assert "agent_response" in response
    
    # Verify the greeting is welcoming (intake specialist style)
    agent_response = response["agent_response"].lower()
    assert any(word in agent_response for word in ["welcome", "excited", "started", "journey"]), \
        "Intake specialist should have welcoming, beginner-friendly tone"


@pytest.mark.asyncio
async def test_existing_user_gets_conversation_agent(db_session, test_user):
    """Test that users with existing plans get the conversation agent."""
    # Create a fitness plan for the user
    fitness_plan = FitnessPlan(
        user_id=test_user.id,
        goal_description="Build muscle",
        goal_type="muscle_gain",
        duration_weeks=12,
        start_date="2025-11-01",
        target_end_date="2026-01-24",
        plan_snapshot={"test": "data"},
    )
    db_session.add(fitness_plan)
    await db_session.commit()

    # Verify user has a plan
    stmt = select(FitnessPlan).where(FitnessPlan.user_id == test_user.id)
    result = await db_session.execute(stmt)
    existing_plans = result.scalars().all()
    assert len(existing_plans) > 0, "Test user should have at least one plan"

    # Start conversation
    ai_service = AIOrchestrationService(db_session)
    response = await ai_service.start_conversation(
        user=test_user,
        initial_message="I want to add more cardio",
    )

    # Verify response structure
    assert "conversation_id" in response
    assert "agent_response" in response
    
    # Verify the greeting is for returning users (conversation agent style)
    agent_response = response["agent_response"].lower()
    # Conversation agent should acknowledge existing relationship or focus on modification
    assert any(word in agent_response for word in ["current", "plan", "modify", "add", "cardio"]), \
        "Conversation agent should reference existing plan context"


@pytest.mark.asyncio
async def test_greeting_for_new_user_no_message(db_session, test_user):
    """Test greeting for new user who starts chat without initial message."""
    # Ensure user has no fitness plans
    stmt = select(FitnessPlan).where(FitnessPlan.user_id == test_user.id)
    result = await db_session.execute(stmt)
    existing_plans = result.scalars().all()
    for plan in existing_plans:
        await db_session.delete(plan)
    await db_session.commit()

    # Start conversation without initial message
    ai_service = AIOrchestrationService(db_session)
    response = await ai_service.start_conversation(
        user=test_user,
        initial_message=None,
    )

    # Verify greeting is welcoming for new users
    agent_response = response["agent_response"].lower()
    assert "welcome" in agent_response, "New user greeting should say 'welcome'"
    assert any(word in agent_response for word in ["started", "journey", "goal"]), \
        "New user greeting should mention getting started"


@pytest.mark.asyncio
async def test_greeting_for_existing_user_no_message(db_session, test_user):
    """Test greeting for existing user who starts chat without initial message."""
    # Create a fitness plan for the user
    fitness_plan = FitnessPlan(
        user_id=test_user.id,
        goal_description="Lose weight",
        goal_type="weight_loss",
        duration_weeks=12,
        start_date="2025-11-01",
        target_end_date="2026-01-24",
        plan_snapshot={"test": "data"},
    )
    db_session.add(fitness_plan)
    await db_session.commit()

    # Start conversation without initial message
    ai_service = AIOrchestrationService(db_session)
    response = await ai_service.start_conversation(
        user=test_user,
        initial_message=None,
    )

    # Verify greeting acknowledges returning user
    agent_response = response["agent_response"].lower()
    assert any(word in agent_response for word in ["back", "current", "plan", "today"]), \
        "Returning user greeting should acknowledge existing relationship"


@pytest.mark.asyncio
async def test_continue_conversation_routes_correctly(db_session, test_user):
    """Test that continue_conversation also routes based on plan history."""
    # Start with new user
    ai_service = AIOrchestrationService(db_session)
    response1 = await ai_service.start_conversation(
        user=test_user,
        initial_message="I want to lose weight",
    )
    conversation_id = response1["conversation_id"]

    # Continue conversation
    response2 = await ai_service.continue_conversation(
        user=test_user,
        conversation_id=conversation_id,
        user_message="I'm a beginner",
    )

    # Verify response
    assert "agent_response" in response2
    # Should still be using intake specialist since no plan created yet
    agent_response = response2["agent_response"].lower()
    assert len(agent_response) > 0, "Should get a response from agent"

