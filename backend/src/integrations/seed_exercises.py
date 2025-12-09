"""Seed exercises into database with embeddings.

This script seeds the curated exercise database into PostgreSQL with
vector embeddings for semantic search using pgvector.

The exercises are stored as standalone records (without workout_id) by creating
a special "seed workout" that serves as a template source for AI agents.

Usage:
    uv run python -m src.integrations.seed_exercises
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import AsyncSessionLocal
from src.integrations.exercise_database import EXERCISE_DATABASE
from src.models.user import User
from src.models.fitness_plan import FitnessPlan, Phase
from src.models.workout import WorkoutPlan, Workout, Exercise


async def generate_embedding(text: str, model: SentenceTransformer) -> list[float]:
    """Generate embedding vector for text using sentence-transformers.
    
    Args:
        text: Text to embed (exercise name + instructions + form cues)
        model: Sentence transformer model
        
    Returns:
        384-dimensional embedding vector as list
    """
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


async def create_seed_user_and_plan(session: AsyncSession) -> tuple[str, str, str, str, str]:
    """Create a seed user, fitness plan, phase, and workout plan for exercises.

    This creates a special "template" structure that exercises can reference.

    Returns:
        Tuple of (user_id, fitness_plan_id, phase_id, workout_plan_id, workout_id)
    """
    # Check if seed user exists
    result = await session.execute(
        select(User).where(User.email == "seed@fitness-bot.internal")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print("Creating seed user...")
        user = User(
            email="seed@fitness-bot.internal",
            password_hash="$2b$12$SEED_USER_NO_LOGIN",  # Unusable password
            name="Exercise Database Seed",
            fitness_level="intermediate",
            dietary_restrictions=[],
            equipment_access=["gym", "home", "bodyweight"],
            timezone="UTC",
        )
        session.add(user)
        await session.flush()
    
    # Check if seed fitness plan exists
    result = await session.execute(
        select(FitnessPlan).where(
            FitnessPlan.user_id == user.id,
            FitnessPlan.goal_type == "exercise_database_seed"
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        print("Creating seed fitness plan...")
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        plan = FitnessPlan(
            user_id=user.id,
            goal_type="exercise_database_seed",
            goal_description="Template exercises for AI agent consumption",
            duration_weeks=0,
            start_date=now,
            end_date=now,
            status="active",
            plan_snapshot={},
        )
        session.add(plan)
        await session.flush()
    
    # Check if seed phase exists
    result = await session.execute(
        select(Phase).where(Phase.fitness_plan_id == plan.id)
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        print("Creating seed phase...")
        phase = Phase(
            fitness_plan_id=plan.id,
            phase_number=1,
            name="Template Phase",
            objectives=["Template exercises"],
            start_date=now,
            end_date=now,
            phase_details={},
        )
        session.add(phase)
        await session.flush()
    
    # Check if seed workout plan exists
    result = await session.execute(
        select(WorkoutPlan).where(WorkoutPlan.fitness_plan_id == plan.id)
    )
    workout_plan = result.scalar_one_or_none()
    
    if not workout_plan:
        print("Creating seed workout plan...")
        workout_plan = WorkoutPlan(
            fitness_plan_id=plan.id,
            frequency_per_week=0,
            progression_strategy="template",
            workout_plan_details={},
        )
        session.add(workout_plan)
        await session.flush()
    
    # Check if seed workout exists
    result = await session.execute(
        select(Workout).where(
            Workout.workout_plan_id == workout_plan.id,
            Workout.name == "Exercise Database Template"
        )
    )
    workout = result.scalar_one_or_none()
    
    if not workout:
        print("Creating seed workout...")
        workout = Workout(
            workout_plan_id=workout_plan.id,
            phase_id=phase.id,
            name="Exercise Database Template",
            workout_type="template",
            duration_minutes=0,
            intensity_level="varies",
            workout_structure={},
        )
        session.add(workout)
        await session.flush()
    
    return str(user.id), str(plan.id), str(phase.id), str(workout_plan.id), str(workout.id)


async def seed_exercises():
    """Seed exercises into database with embeddings."""
    print("=" * 80)
    print("Exercise Database Seeding Script")
    print("=" * 80)
    print()
    
    # Load sentence transformer model
    print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print(f"✓ Model loaded (embedding dimension: 384)")
    print()
    
    async with AsyncSessionLocal() as session:
        # Create seed infrastructure
        user_id, plan_id, phase_id, workout_plan_id, workout_id = await create_seed_user_and_plan(session)
        print(f"✓ Seed infrastructure ready (workout_id: {workout_id})")
        print()
        
        # Check existing exercises
        result = await session.execute(
            select(Exercise).where(Exercise.workout_id == workout_id)
        )
        existing_exercises = result.scalars().all()
        existing_names = {ex.name for ex in existing_exercises}
        
        if existing_exercises:
            print(f"Found {len(existing_exercises)} existing exercises in database")
            print(f"Will seed {len(EXERCISE_DATABASE) - len(existing_names)} new exercises")
            print()
        
        # Seed exercises
        seeded_count = 0
        updated_count = 0
        
        for idx, exercise_data in enumerate(EXERCISE_DATABASE, 1):
            exercise_name = exercise_data["name"]
            
            # Create embedding text from name, instructions, and form cues
            embedding_text = f"{exercise_name}. "
            embedding_text += exercise_data["instructions"] + " "
            if exercise_data.get("form_cues"):
                embedding_text += " ".join(exercise_data["form_cues"])
            
            # Generate embedding
            embedding = await generate_embedding(embedding_text, model)
            
            if exercise_name in existing_names:
                # Update existing exercise with embedding if missing
                result = await session.execute(
                    select(Exercise).where(
                        Exercise.workout_id == workout_id,
                        Exercise.name == exercise_name
                    )
                )
                exercise = result.scalar_one()
                
                if exercise.embedding is None:
                    exercise.embedding = embedding
                    updated_count += 1
                    print(f"[{idx}/{len(EXERCISE_DATABASE)}] Updated embedding: {exercise_name}")
            else:
                # Create new exercise
                exercise = Exercise(
                    workout_id=workout_id,
                    exercise_order=idx,
                    name=exercise_name,
                    exercise_type=exercise_data["exercise_type"],
                    target_muscle_groups=exercise_data["target_muscle_groups"],
                    equipment_required=exercise_data["equipment_required"],
                    sets=3,  # Default template values
                    reps="8-12",
                    duration_seconds=None,
                    rest_seconds=90,
                    tempo="3-0-1",
                    rpe_target=7,
                    instructions=exercise_data["instructions"],
                    form_cues=exercise_data.get("form_cues", []),
                    alternative_exercise_ids=None,  # Will be populated later
                    embedding=embedding,
                )
                session.add(exercise)
                seeded_count += 1
                print(f"[{idx}/{len(EXERCISE_DATABASE)}] Seeded: {exercise_name}")
        
        # Commit all exercises
        await session.commit()
        
        print()
        print("=" * 80)
        print(f"✓ Seeding complete!")
        print(f"  - New exercises seeded: {seeded_count}")
        print(f"  - Embeddings updated: {updated_count}")
        print(f"  - Total exercises in database: {len(existing_names) + seeded_count}")
        print()
        print("Exercises are now searchable by semantic meaning using pgvector!")
        print("=" * 80)


async def verify_seeding():
    """Verify that exercises were seeded correctly."""
    print()
    print("=" * 80)
    print("Verification")
    print("=" * 80)
    
    async with AsyncSessionLocal() as session:
        # Count total exercises
        result = await session.execute(select(Exercise))
        exercises = result.scalars().all()
        
        print(f"\nTotal exercises in database: {len(exercises)}")
        
        # Count exercises with embeddings
        exercises_with_embeddings = [ex for ex in exercises if ex.embedding is not None]
        print(f"Exercises with embeddings: {len(exercises_with_embeddings)}")
        
        # Show sample exercises
        if exercises:
            print("\nSample exercises:")
            for ex in exercises[:5]:
                has_embedding = "✓" if ex.embedding else "✗"
                print(f"  {has_embedding} {ex.name} ({ex.exercise_type}, {ex.target_muscle_groups[0]})")
        
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(seed_exercises())
    asyncio.run(verify_seeding())
