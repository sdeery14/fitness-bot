"""Integration test for automatic schedule creation when fitness plan is saved.

This test verifies that when a fitness plan is created and saved with AI-generated
content, a schedule is automatically created that spans the entire plan duration.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.fitness_plan import FitnessPlan
from src.models.meal import Meal, MealPlan
from src.models.schedule import Schedule, ScheduleEntry
from src.models.user import User
from src.models.workout import Workout, WorkoutPlan
from src.services.plan_service import PlanService


@pytest.mark.asyncio
async def test_automatic_schedule_creation_on_plan_save(db_session: AsyncSession):
    """Test that schedule is automatically created when plan is saved with complete data.

    Scenario:
    1. Create a user and fitness plan
    2. Save AI-generated plan data (workouts and meals)
    3. Verify schedule is automatically created
    4. Verify schedule entries span entire plan duration
    5. Verify both workout and meal entries exist
    """
    # Create test user
    user = User(
        email=f"test_schedule_{uuid4()}@example.com",
        password_hash="test_hash",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create fitness plan (12 weeks for training)
    plan_duration_weeks = 12
    start_date = date.today()
    end_date = start_date + timedelta(weeks=plan_duration_weeks)

    plan = FitnessPlan(
        user_id=user.id,
        goal="Train for 5K race",
        start_date=start_date,
        end_date=end_date,
        duration_weeks=plan_duration_weeks,
        status="draft",
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    # Create AI-generated plan output structure
    plan_output = {
        "goal_summary": "12-week 5K training plan with progressive running and strength work",
        "duration_weeks": plan_duration_weeks,
        "fitness_level": "intermediate",
        "workout_plan_output": {
            "workout_plan": {
                "frequency_per_week": 4,
                "program_type": "Running Training",
                "duration_weeks": plan_duration_weeks,
                "progression_notes": "Increase weekly mileage by 10% each week",
                "workouts": [
                    {
                        "day_name": "Monday - Easy Run",
                        "focus": "Aerobic Base",
                        "duration_minutes": 30,
                        "exercises": []
                    },
                    {
                        "day_name": "Wednesday - Tempo Run",
                        "focus": "Speed Endurance",
                        "duration_minutes": 40,
                        "exercises": []
                    },
                    {
                        "day_name": "Friday - Intervals",
                        "focus": "Speed Work",
                        "duration_minutes": 45,
                        "exercises": []
                    },
                    {
                        "day_name": "Sunday - Long Run",
                        "focus": "Endurance",
                        "duration_minutes": 60,
                        "exercises": []
                    }
                ],
                "training_cycle": [
                    {"type": "workout", "workout_index": 0},
                    {"type": "rest", "rest_day": {"day_name": "Rest Day"}},
                    {"type": "workout", "workout_index": 1},
                    {"type": "rest", "rest_day": {"day_name": "Rest Day"}},
                    {"type": "workout", "workout_index": 2},
                    {"type": "rest", "rest_day": {"day_name": "Rest Day"}},
                    {"type": "workout", "workout_index": 3}
                ]
            },
            "key_exercises": ["Running", "Intervals", "Tempo"],
            "equipment_used": ["Running shoes", "Watch"]
        },
        "meal_plan_output": {
            "meal_plan": {
                "daily_calorie_target": 2200,
                "macro_split": "45% Carbs, 25% Protein, 30% Fat",
                "meal_frequency": 3,
                "sample_days": [
                    {
                        "day_name": "Training Day",
                        "meals": [
                            {"meal_name": "Breakfast", "foods": []},
                            {"meal_name": "Lunch", "foods": []},
                            {"meal_name": "Dinner", "foods": []}
                        ]
                    }
                ]
            },
            "key_foods": ["Oatmeal", "Chicken", "Rice"],
            "prep_difficulty": "Medium"
        },
        "key_principles": ["Progressive overload", "Adequate recovery", "Proper nutrition"],
        "success_metrics": ["Complete all runs", "Increase distance weekly", "Finish 5K race"],
        "important_notes": "Listen to your body and adjust as needed"
    }

    # Create workouts for the plan
    workout_plan = WorkoutPlan(
        fitness_plan_id=plan.id,
        frequency_per_week=4,
        progression_strategy="Progressive overload",
        workout_plan_details=plan_output["workout_plan_output"]["workout_plan"]
    )
    db_session.add(workout_plan)
    await db_session.flush()

    # Create sample workouts
    workout1 = Workout(
        workout_plan_id=workout_plan.id,
        name="Easy Run",
        workout_type="cardio",
        duration_minutes=30,
        intensity_level="moderate",
    )
    workout2 = Workout(
        workout_plan_id=workout_plan.id,
        name="Tempo Run",
        workout_type="cardio",
        duration_minutes=40,
        intensity_level="high",
    )
    db_session.add_all([workout1, workout2])
    await db_session.flush()

    # Create meal plan
    meal_plan = MealPlan(
        fitness_plan_id=plan.id,
        daily_calorie_target=2200,
        macronutrient_distribution={"macro_split": "45% Carbs, 25% Protein, 30% Fat"},
        meals_per_day=3,
    )
    db_session.add(meal_plan)
    await db_session.flush()

    # Create sample meals
    meal1 = Meal(
        meal_plan_id=meal_plan.id,
        name="Breakfast",
        meal_type="breakfast",
        calories=600,
    )
    meal2 = Meal(
        meal_plan_id=meal_plan.id,
        name="Lunch",
        meal_type="lunch",
        calories=800,
    )
    meal3 = Meal(
        meal_plan_id=meal_plan.id,
        name="Dinner",
        meal_type="dinner",
        calories=800,
    )
    db_session.add_all([meal1, meal2, meal3])
    await db_session.commit()

    # Save the generated plan using PlanService
    # This should automatically create the schedule
    plan_service = PlanService(db_session)
    await plan_service.save_generated_plan(
        plan_id=plan.id,
        plan_output=plan_output
    )

    # Verify schedule was created
    schedule_stmt = select(Schedule).where(Schedule.fitness_plan_id == plan.id)
    schedule_result = await db_session.execute(schedule_stmt)
    schedule = schedule_result.scalar_one_or_none()

    assert schedule is not None, "Schedule should be automatically created"
    assert schedule.user_id == user.id
    assert schedule.fitness_plan_id == plan.id
    assert schedule.start_date == start_date

    # Verify schedule entries were created
    entries_stmt = select(ScheduleEntry).where(ScheduleEntry.schedule_id == schedule.id)
    entries_result = await db_session.execute(entries_stmt)
    entries = list(entries_result.scalars().all())

    assert len(entries) > 0, "Schedule entries should be created"

    # Verify workout entries exist
    workout_entries = [e for e in entries if e.entry_type == "workout"]
    assert len(workout_entries) > 0, "Workout schedule entries should exist"

    # Verify meal entries exist
    meal_entries = [e for e in entries if e.entry_type == "meal"]
    assert len(meal_entries) > 0, "Meal schedule entries should exist"

    # Verify entries span entire plan duration
    earliest_entry = min(e.entry_date for e in entries)
    latest_entry = max(e.entry_date for e in entries)

    assert earliest_entry >= start_date, "Entries should start at or after plan start date"
    assert latest_entry <= end_date, "Entries should not exceed plan end date"

    # Verify coverage is close to full duration (within a week of end date)
    # This accounts for weekly workout schedules that may not land exactly on end_date
    days_covered = (latest_entry - earliest_entry).days
    expected_days = (end_date - start_date).days
    coverage_ratio = days_covered / expected_days if expected_days > 0 else 0

    assert coverage_ratio >= 0.90, f"Schedule should cover at least 90% of plan duration (covers {coverage_ratio*100:.1f}%)"

    # Verify meal entries are daily (should be close to plan duration in days)
    meal_days = len({e.entry_date for e in meal_entries})
    expected_meal_days = plan_duration_weeks * 7
    meal_coverage_ratio = meal_days / expected_meal_days if expected_meal_days > 0 else 0

    assert meal_coverage_ratio >= 0.95, f"Meal entries should cover at least 95% of days (covers {meal_coverage_ratio*100:.1f}%)"

    print(f"✓ Schedule created with {len(entries)} entries")
    print(f"✓ {len(workout_entries)} workout entries spanning {days_covered} days")
    print(f"✓ {len(meal_entries)} meal entries covering {meal_days} days")
    print(f"✓ Coverage: {coverage_ratio*100:.1f}% of plan duration")


@pytest.mark.asyncio
async def test_schedule_not_duplicated_on_multiple_saves(db_session: AsyncSession):
    """Test that schedule is only created once, even if plan is saved multiple times.

    Scenario:
    1. Create a user and fitness plan
    2. Save AI-generated plan data (first time)
    3. Save plan data again (second time)
    4. Verify only one schedule exists
    """
    # Create test user
    user = User(
        email=f"test_no_duplicate_{uuid4()}@example.com",
        password_hash="test_hash",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create fitness plan
    plan_duration_weeks = 8
    start_date = date.today()
    end_date = start_date + timedelta(weeks=plan_duration_weeks)

    plan = FitnessPlan(
        user_id=user.id,
        goal="Weight loss program",
        start_date=start_date,
        end_date=end_date,
        duration_weeks=plan_duration_weeks,
        status="draft",
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    # Minimal plan output
    plan_output = {
        "goal_summary": "8-week weight loss plan",
        "duration_weeks": plan_duration_weeks,
        "fitness_level": "beginner",
        "workout_plan_output": {
            "workout_plan": {
                "frequency_per_week": 3,
                "workouts": [],
                "training_cycle": []
            },
            "key_exercises": [],
            "equipment_used": []
        },
        "meal_plan_output": {
            "meal_plan": {
                "daily_calorie_target": 1800,
                "macro_split": "40% Carbs, 30% Protein, 30% Fat",
                "meal_frequency": 3,
            },
            "key_foods": [],
            "prep_difficulty": "Easy"
        },
        "key_principles": [],
        "success_metrics": [],
        "important_notes": ""
    }

    # Save plan first time
    plan_service = PlanService(db_session)
    await plan_service.save_generated_plan(plan_id=plan.id, plan_output=plan_output)

    # Verify schedule was created
    schedule_stmt = select(Schedule).where(Schedule.fitness_plan_id == plan.id)
    schedule_result = await db_session.execute(schedule_stmt)
    schedules_first = list(schedule_result.scalars().all())
    assert len(schedules_first) == 1, "Should have exactly one schedule after first save"

    # Save plan second time (simulating update)
    await plan_service.save_generated_plan(plan_id=plan.id, plan_output=plan_output)

    # Verify still only one schedule
    schedule_result2 = await db_session.execute(schedule_stmt)
    schedules_second = list(schedule_result2.scalars().all())
    assert len(schedules_second) == 1, "Should still have exactly one schedule after second save"
    assert schedules_first[0].id == schedules_second[0].id, "Should be the same schedule"

    print("✓ Schedule not duplicated on multiple saves")
