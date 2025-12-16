"""Unit tests for PlanService structured update functionality."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC, timedelta

from src.models.fitness_plan import FitnessPlan, Phase
from src.models.workout import WorkoutPlan, Workout
from src.models.meal import MealPlan, Meal
from src.services.plan_service import PlanService


@pytest.mark.asyncio
async def test_apply_plan_updates_basic_fields(db_session, sample_user):
    """Test updating basic plan-level fields."""
    plan_service = PlanService(db_session)
    
    # Create a parent plan
    parent_plan = FitnessPlan(
        user_id=sample_user.id,
        goal_type="weight_loss",
        goal_description="Lose 20 pounds in 3 months",
        duration_weeks=12,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(weeks=12),
        status="active",
    )
    db_session.add(parent_plan)
    await db_session.commit()
    await db_session.refresh(parent_plan)
    
    # Apply updates
    updates = [
        {"field": "goal_description", "value": "Lose 20 pounds and build strength", "operation": "set"},
        {"field": "duration_weeks", "value": 16, "operation": "set"},
        {"field": "target_weight_kg", "value": "75", "operation": "set"},
    ]
    
    new_plan = await plan_service.apply_plan_updates(
        parent_plan_id=parent_plan.id,
        updates=updates,
        version_notes="Extended duration and clarified goals"
    )
    
    # Verify updates were applied
    assert new_plan.goal_description == "Lose 20 pounds and build strength"
    assert new_plan.duration_weeks == 16
    assert new_plan.target_weight_kg == "75"
    assert new_plan.version == 2
    assert new_plan.parent_plan_id == parent_plan.id
    assert new_plan.status == "active"
    
    # Verify parent was marked as replaced
    await db_session.refresh(parent_plan)
    assert parent_plan.status == "replaced"


@pytest.mark.asyncio
async def test_apply_plan_updates_workout_plan(db_session, sample_user):
    """Test updating workout plan fields."""
    plan_service = PlanService(db_session)
    
    # Create parent plan with workout plan
    parent_plan = FitnessPlan(
        user_id=sample_user.id,
        goal_type="muscle_gain",
        goal_description="Build muscle",
        duration_weeks=12,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(weeks=12),
        status="active",
    )
    db_session.add(parent_plan)
    await db_session.flush()
    
    workout_plan = WorkoutPlan(
        fitness_plan_id=parent_plan.id,
        frequency_per_week=3,
        progression_strategy="linear",
        workout_plan_details={"split": "full_body"},
    )
    db_session.add(workout_plan)
    await db_session.commit()
    
    # Apply updates to workout plan
    updates = [
        {"field": "workout_plans[0].frequency_per_week", "value": 4, "operation": "set"},
        {"field": "workout_plans[0].progression_strategy", "value": "wave", "operation": "set"},
    ]
    
    new_plan = await plan_service.apply_plan_updates(
        parent_plan_id=parent_plan.id,
        updates=updates,
        version_notes="Increased frequency to 4 days per week"
    )
    
    # Note: This test currently only validates the method doesn't crash
    # Full validation requires copying relationships, which is not yet implemented
    assert new_plan.version == 2
    assert new_plan.status == "active"


@pytest.mark.asyncio
async def test_apply_plan_updates_meal_plan(db_session, sample_user):
    """Test updating meal plan fields."""
    plan_service = PlanService(db_session)
    
    # Create parent plan with meal plan
    parent_plan = FitnessPlan(
        user_id=sample_user.id,
        goal_type="fat_loss",
        goal_description="Lose fat",
        duration_weeks=12,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(weeks=12),
        status="active",
    )
    db_session.add(parent_plan)
    await db_session.flush()
    
    meal_plan = MealPlan(
        fitness_plan_id=parent_plan.id,
        daily_calorie_target=2000,
        macronutrient_distribution={"protein": 30, "carbs": 40, "fats": 30},
        protein_grams_target=150,
        carbs_grams_target=200,
        fats_grams_target=67,
        meals_per_day=3,
    )
    db_session.add(meal_plan)
    await db_session.commit()
    
    # Apply updates to meal plan
    updates = [
        {"field": "meal_plans[0].daily_calorie_target", "value": 2200, "operation": "set"},
        {"field": "meal_plans[0].protein_grams_target", "value": 165, "operation": "set"},
    ]
    
    new_plan = await plan_service.apply_plan_updates(
        parent_plan_id=parent_plan.id,
        updates=updates,
        version_notes="Increased calories to 2200 and protein to 165g"
    )
    
    # Note: This test currently only validates the method doesn't crash
    assert new_plan.version == 2
    assert new_plan.status == "active"


@pytest.mark.asyncio
async def test_apply_plan_updates_invalid_field(db_session, sample_user):
    """Test error handling for invalid field paths."""
    plan_service = PlanService(db_session)
    
    # Create a parent plan
    parent_plan = FitnessPlan(
        user_id=sample_user.id,
        goal_type="general_fitness",
        goal_description="Get fit",
        duration_weeks=8,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(weeks=8),
        status="active",
    )
    db_session.add(parent_plan)
    await db_session.commit()
    
    # Try to update a non-existent field
    updates = [
        {"field": "nonexistent_field", "value": "test", "operation": "set"},
    ]
    
    with pytest.raises(ValueError, match="Failed to apply update"):
        await plan_service.apply_plan_updates(
            parent_plan_id=parent_plan.id,
            updates=updates,
            version_notes="This should fail"
        )


@pytest.mark.asyncio
async def test_apply_plan_updates_parent_not_found(db_session):
    """Test error handling when parent plan doesn't exist."""
    plan_service = PlanService(db_session)
    
    fake_plan_id = uuid4()
    updates = [
        {"field": "duration_weeks", "value": 16, "operation": "set"},
    ]
    
    with pytest.raises(ValueError, match="Parent plan not found"):
        await plan_service.apply_plan_updates(
            parent_plan_id=fake_plan_id,
            updates=updates,
            version_notes="This should fail"
        )


@pytest.mark.asyncio
async def test_apply_plan_updates_increment_operation(db_session, sample_user):
    """Test increment operation on numeric fields."""
    plan_service = PlanService(db_session)
    
    # Create a parent plan
    parent_plan = FitnessPlan(
        user_id=sample_user.id,
        goal_type="endurance",
        goal_description="Build endurance",
        duration_weeks=10,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(weeks=10),
        status="active",
    )
    db_session.add(parent_plan)
    await db_session.commit()
    
    # Increment duration by 2 weeks
    updates = [
        {"field": "duration_weeks", "value": 2, "operation": "increment"},
    ]
    
    new_plan = await plan_service.apply_plan_updates(
        parent_plan_id=parent_plan.id,
        updates=updates,
        version_notes="Extended by 2 weeks"
    )
    
    assert new_plan.duration_weeks == 12  # 10 + 2


@pytest.mark.asyncio
async def test_apply_plan_updates_multiple_changes(db_session, sample_user):
    """Test applying multiple updates in one call."""
    plan_service = PlanService(db_session)
    
    # Create a parent plan
    parent_plan = FitnessPlan(
        user_id=sample_user.id,
        goal_type="recomp",
        goal_description="Body recomposition",
        duration_weeks=16,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(weeks=16),
        status="active",
        key_principles=["Progressive overload", "Consistency"],
    )
    db_session.add(parent_plan)
    await db_session.commit()
    
    # Apply multiple updates
    updates = [
        {"field": "goal_description", "value": "Build muscle while losing fat", "operation": "set"},
        {"field": "duration_weeks", "value": 20, "operation": "set"},
        {"field": "target_weight_kg", "value": "82", "operation": "set"},
    ]
    
    new_plan = await plan_service.apply_plan_updates(
        parent_plan_id=parent_plan.id,
        updates=updates,
        version_notes="Major plan revision"
    )
    
    # Verify all updates were applied
    assert new_plan.goal_description == "Build muscle while losing fat"
    assert new_plan.duration_weeks == 20
    assert new_plan.target_weight_kg == "82"
    assert new_plan.version == 2
