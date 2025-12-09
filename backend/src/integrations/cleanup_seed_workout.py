"""Clean up old seed workout data now that exercise_catalog exists.

This script removes the temporary seed user, fitness plan, and workout that
were used to store exercises before the exercise_catalog table was created.

Usage:
    docker-compose -f docker/docker-compose.yml exec backend python -m src.integrations.cleanup_seed_workout
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from src.database import AsyncSessionLocal
from src.models.fitness_plan import FitnessPlan
from src.models.user import User


async def cleanup_seed_data():
    """Remove seed user and associated fitness plan/workout/exercises."""
    print("=" * 60)
    print("CLEANING UP OLD SEED WORKOUT DATA")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Find seed user
        result = await session.execute(
            select(User).where(User.email == "seed@fitness-bot.internal")
        )
        seed_user = result.scalar_one_or_none()

        if not seed_user:
            print("\n✓ No seed user found - already cleaned up")
            return

        print(f"\n1. Found seed user: {seed_user.email} (ID: {seed_user.id})")

        # Find seed fitness plan
        result = await session.execute(
            select(FitnessPlan).where(
                FitnessPlan.user_id == seed_user.id,
                FitnessPlan.goal_type == "exercise_database_seed"
            )
        )
        seed_plan = result.scalar_one_or_none()

        if seed_plan:
            print(f"2. Found seed fitness plan (ID: {seed_plan.id})")

        # Count associated records before deletion
        from src.models.fitness_plan import Phase
        from src.models.workout import Exercise, Workout, WorkoutPlan

        if seed_plan:
            # Count workout plans
            result = await session.execute(
                select(WorkoutPlan).where(WorkoutPlan.fitness_plan_id == seed_plan.id)
            )
            workout_plans = result.scalars().all()
            print(f"   - {len(workout_plans)} workout plan(s)")

            # Count phases
            result = await session.execute(
                select(Phase).where(Phase.fitness_plan_id == seed_plan.id)
            )
            phases = result.scalars().all()
            print(f"   - {len(phases)} phase(s)")

            # Count workouts
            workout_ids = []
            for phase in phases:
                result = await session.execute(
                    select(Workout).where(Workout.phase_id == phase.id)
                )
                workouts = result.scalars().all()
                workout_ids.extend([w.id for w in workouts])
            print(f"   - {len(workout_ids)} workout(s)")

            # Count exercises
            exercise_count = 0
            for workout_id in workout_ids:
                result = await session.execute(
                    select(Exercise).where(Exercise.workout_id == workout_id)
                )
                exercises = result.scalars().all()
                exercise_count += len(exercises)
            print(f"   - {exercise_count} exercise(s)")

        # Confirm deletion
        print("\n3. Deleting seed user (cascades to all associated records)...")
        response = input("   Continue? (yes/no): ")

        if response.lower() != "yes":
            print("   ✗ Cancelled")
            return

        # Delete seed user (cascades to fitness_plans, phases, workout_plans, workouts, exercises)
        await session.delete(seed_user)
        await session.commit()
        print("   ✓ Deleted")

        # Verify deletion
        result = await session.execute(select(Exercise))
        remaining_exercises = len(result.scalars().all())

        result = await session.execute(select(Workout))
        remaining_workouts = len(result.scalars().all())

        print("\n4. Verification:")
        print(f"   - Remaining exercises: {remaining_exercises}")
        print(f"   - Remaining workouts: {remaining_workouts}")

        print("\n" + "=" * 60)
        print("✓ CLEANUP COMPLETE")
        print("=" * 60)
        print("\nThe exercises and workouts tables are now ready for user plans.")
        print("Curated exercises are available in exercise_catalog table.")


if __name__ == "__main__":
    asyncio.run(cleanup_seed_data())
