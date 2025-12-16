"""Test that plan updates now copy phases/workouts/exercises."""
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.services.plan_service import PlanService

DATABASE_URL = "postgresql+asyncpg://fitness_user:fitness_pass_dev@localhost:5432/fitness_bot"

async def test_phase_copy():
    """Test that phases, workouts, and exercises are copied in version updates."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        plan_service = PlanService(session)
        
        # Use the plan that has the Full Body -> Upper/Lower update issue
        # Version 1 has workouts, version 2 is empty
        parent_plan_id = UUID("05dbc845-0f88-4a11-86a8-dfb507685ae1")
        
        # Create a new version with a simple metadata update
        updates = [
            {
                "field": "workout_plans[0].program_type",
                "value": "Upper/Lower Split - Fixed",
                "operation": "set"
            }
        ]
        
        try:
            new_plan = await plan_service.apply_plan_updates(
                parent_plan_id=parent_plan_id,
                updates=updates,
                version_notes="Testing phase/workout/exercise deep copy"
            )
            
            # Eagerly load all relationships
            await session.refresh(new_plan, ["workout_plans", "meal_plans", "phases"])
            
            print(f"✓ Created new plan version: {new_plan.id}")
            print(f"  Program type: {new_plan.workout_plans[0].program_type}")
            print(f"  Phases count: {len(new_plan.phases)}")
            
            # Count workouts and exercises
            total_workouts = 0
            total_exercises = 0
            for phase in new_plan.phases:
                await session.refresh(phase, ["workouts"])
                phase_workouts = len(phase.workouts)
                total_workouts += phase_workouts
                
                for workout in phase.workouts:
                    await session.refresh(workout, ["exercises"])
                    total_exercises += len(workout.exercises)
                    print(f"  Phase '{phase.name}' - Workout '{workout.name}': {len(workout.exercises)} exercises")
            
            print(f"\n✓ Total workouts: {total_workouts}")
            print(f"✓ Total exercises: {total_exercises}")
            
            if total_workouts > 0 and total_exercises > 0:
                print("\n✅ SUCCESS: Phases, workouts, and exercises were copied!")
            else:
                print("\n❌ FAILED: No workouts or exercises found in new version")
            
        except Exception as e:
            print(f"❌ Update failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_phase_copy())
