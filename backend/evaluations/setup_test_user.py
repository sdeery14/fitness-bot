"""Setup test user with fitness plan data for evaluation."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.user import User
from src.models.fitness_plan import FitnessPlan, Phase
from src.models.workout import WorkoutPlan, Workout, Exercise


async def create_test_user_with_plan():
    """Create a test user with a complete fitness plan for evaluation.
    
    Returns:
        str: The user_id (UUID) of the created test user
    """
    # Use the same database connection as the running backend
    engine = create_async_engine(
        "postgresql+asyncpg://fitness_user:fitness_pass_dev@localhost:5432/fitness_bot",
        echo=False
    )
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if test user already exists
        result = await session.execute(
            select(User).where(User.email == "eval_test_user@fitness.ai")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"✓ Test user already exists: {existing_user.id}")
            return str(existing_user.id)
        
        # Create test user
        test_user = User(
            id=uuid4(),
            email="eval_test_user@fitness.ai",
            password_hash="$2b$12$dummy_hash_for_test_user_only",  # Won't be used for login
            name="Evaluation Test User",
            date_of_birth=datetime(1990, 1, 1),
            gender="male",
            height_cm="178",
            weight_kg="80",
            fitness_level="intermediate",
            activity_level="moderately_active",
            equipment_access=["dumbbells", "barbell", "bench", "pull_up_bar"],
            dietary_restrictions=[],
            preferences={},
            timezone="America/New_York",
            is_active=True
        )
        session.add(test_user)
        
        # Create fitness plan
        start_date = datetime.now().date()
        end_date = start_date + timedelta(weeks=12)
        
        fitness_plan = FitnessPlan(
            id=uuid4(),
            user_id=test_user.id,
            goal_type="muscle_gain",
            goal_description="12-Week Muscle Building Program",
            duration_weeks=12,
            start_date=start_date,
            end_date=end_date,
            status="active",
            key_principles=[
                "Progressive overload with compound movements",
                "High protein intake (1g per lb bodyweight)",
                "4 training days per week with adequate recovery"
            ],
            success_metrics=[
                "Increase weight by 10-15 pounds",
                "Improve main lifts by 20%",
                "Maintain body fat percentage"
            ],
            important_notes=[
                "Focus on form over weight",
                "Track all workouts in app",
                "Get 7-8 hours of sleep"
            ]
        )
        session.add(fitness_plan)
        
        # Create phases
        phase1 = Phase(
            id=uuid4(),
            fitness_plan_id=fitness_plan.id,
            phase_number=1,
            name="Foundation Phase",
            start_date=start_date,
            end_date=start_date + timedelta(weeks=4),
            objectives=[
                "Build strength foundation",
                "Perfect form on compound lifts",
                "Establish workout routine"
            ],
            phase_details={
                "duration_weeks": 4,
                "training_focus": "Strength and technique",
                "nutrition_focus": "Increase calories by 200-300 above maintenance",
                "intensity_level": "moderate"
            }
        )
        
        phase2 = Phase(
            id=uuid4(),
            fitness_plan_id=fitness_plan.id,
            phase_number=2,
            name="Hypertrophy Phase",
            start_date=start_date + timedelta(weeks=4),
            end_date=start_date + timedelta(weeks=8),
            objectives=[
                "Increase training volume",
                "Target muscle groups with isolation work",
                "Continue progressive overload"
            ],
            phase_details={
                "duration_weeks": 4,
                "training_focus": "Muscle hypertrophy with higher volume",
                "nutrition_focus": "Maintain calorie surplus, track protein",
                "intensity_level": "high"
            }
        )
        
        phase3 = Phase(
            id=uuid4(),
            fitness_plan_id=fitness_plan.id,
            phase_number=3,
            name="Strength Phase",
            start_date=start_date + timedelta(weeks=8),
            end_date=end_date,
            objectives=[
                "Maximize strength gains",
                "Peak performance on main lifts",
                "Consolidate muscle gains"
            ],
            phase_details={
                "duration_weeks": 4,
                "training_focus": "Heavy compound movements, lower reps",
                "nutrition_focus": "High protein, moderate surplus",
                "intensity_level": "very_high"
            }
        )
        
        session.add_all([phase1, phase2, phase3])
        
        # Create workout plan
        workout_plan = WorkoutPlan(
            id=uuid4(),
            fitness_plan_id=fitness_plan.id,
            frequency_per_week=4,
            progression_strategy="linear",
            program_type="Upper/Lower Split",
            training_principles=["Progressive overload", "Mind-muscle connection", "Proper form"],
            equipment_used=["barbell", "dumbbells", "bench", "pull_up_bar"]
        )
        session.add(workout_plan)
        
        # Create sample workouts for Foundation Phase
        workouts = [
            Workout(
                id=uuid4(),
                workout_plan_id=workout_plan.id,
                phase_id=phase1.id,
                name="Upper Body A",
                workout_type="strength",
                duration_minutes=60,
                intensity_level="moderate",
                workout_structure={
                    "warm_up": "5 min cardio, dynamic stretching",
                    "main_work": "4 exercises, compound focus",
                    "cool_down": "5 min stretching"
                }
            ),
            Workout(
                id=uuid4(),
                workout_plan_id=workout_plan.id,
                phase_id=phase1.id,
                name="Lower Body A",
                workout_type="strength",
                duration_minutes=60,
                intensity_level="high",
                workout_structure={
                    "warm_up": "5 min cardio, leg swings",
                    "main_work": "3 exercises, squat focus",
                    "cool_down": "5 min stretching"
                }
            ),
            Workout(
                id=uuid4(),
                workout_plan_id=workout_plan.id,
                phase_id=phase1.id,
                name="Upper Body B",
                workout_type="strength",
                duration_minutes=55,
                intensity_level="moderate",
                workout_structure={
                    "warm_up": "Band pull-aparts, shoulder circles",
                    "main_work": "3 exercises, pressing and pulling",
                    "cool_down": "Shoulder stretching"
                }
            ),
            Workout(
                id=uuid4(),
                workout_plan_id=workout_plan.id,
                phase_id=phase1.id,
                name="Lower Body B",
                workout_type="strength",
                duration_minutes=65,
                intensity_level="high",
                workout_structure={
                    "warm_up": "5 min cardio, hip mobility",
                    "main_work": "3 exercises, deadlift focus",
                    "cool_down": "Lower body stretching"
                }
            )
        ]
        session.add_all(workouts)
        
        await session.commit()
        
        print(f"✓ Created test user: {test_user.id}")
        print(f"  Email: {test_user.email}")
        print(f"  Fitness Plan: {fitness_plan.goal_description}")
        print(f"  Phases: {len([phase1, phase2, phase3])}")
        print(f"  Workouts: {len(workouts)}")
        print(f"  Current Phase: {phase1.phase_name}")
        
        return str(test_user.id)
    
    await engine.dispose()


if __name__ == "__main__":
    print("="*80)
    print("Setting up test user with fitness plan for evaluation")
    print("="*80)
    print()
    
    user_id = asyncio.run(create_test_user_with_plan())
    
    print()
    print("="*80)
    print("Test user ready for evaluation!")
    print("="*80)
    print(f"User ID: {user_id}")
    print()
    print("Update agent_runners.py to use this user_id for fitness_coach evaluations")
