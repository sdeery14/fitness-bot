"""Seed exercise catalog with curated exercises and embeddings.

This script seeds the exercise_catalog table with the curated exercises
from exercise_database.py, including vector embeddings for semantic search.

Usage:
    docker-compose -f docker/docker-compose.yml exec backend python -m src.integrations.seed_exercise_catalog
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from src.database import AsyncSessionLocal
from src.integrations.exercise_database import EXERCISE_DATABASE
from src.models.exercise_catalog import ExerciseCatalog


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


async def seed_exercise_catalog():
    """Seed exercise_catalog table with curated exercises."""
    print("=" * 60)
    print("SEEDING EXERCISE CATALOG")
    print("=" * 60)
    
    # Load sentence transformer model for embeddings
    print("\n1. Loading sentence-transformers model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("   ✓ Model loaded")
    
    async with AsyncSessionLocal() as session:
        # Check how many exercises already exist
        result = await session.execute(select(ExerciseCatalog))
        existing_count = len(result.scalars().all())
        
        if existing_count > 0:
            print(f"\n⚠ Warning: {existing_count} exercises already exist in catalog")
            response = input("   Delete and re-seed? (yes/no): ")
            if response.lower() == "yes":
                print("   Deleting existing exercises...")
                await session.execute("DELETE FROM exercise_catalog")
                await session.commit()
                print("   ✓ Deleted")
            else:
                print("   Keeping existing exercises")
                return
        
        print(f"\n2. Seeding {len(EXERCISE_DATABASE)} exercises...")
        
        for i, exercise_data in enumerate(EXERCISE_DATABASE, 1):
            # Create embedding text from exercise data
            embedding_text = f"{exercise_data['name']} {exercise_data['instructions']}"
            if exercise_data.get('form_cues'):
                embedding_text += " " + " ".join(exercise_data['form_cues'])
            
            # Generate embedding
            embedding = await generate_embedding(embedding_text, model)
            
            # Create exercise catalog entry
            exercise = ExerciseCatalog(
                id=uuid4(),
                name=exercise_data['name'],
                exercise_type=exercise_data['exercise_type'],
                target_muscle_groups=exercise_data['target_muscle_groups'],
                equipment_required=exercise_data['equipment_required'],
                difficulty=exercise_data['difficulty'],
                instructions=exercise_data['instructions'],
                form_cues=exercise_data.get('form_cues'),
                alternatives=exercise_data.get('alternatives'),
                embedding=embedding,
            )
            
            session.add(exercise)
            
            if i % 10 == 0:
                print(f"   Seeded {i}/{len(EXERCISE_DATABASE)} exercises...")
        
        await session.commit()
        print(f"   ✓ Seeded {len(EXERCISE_DATABASE)} exercises")
        
        # Verify count
        result = await session.execute(select(ExerciseCatalog))
        final_count = len(result.scalars().all())
        print(f"\n3. Verification: {final_count} exercises in catalog")
        
        print("\n" + "=" * 60)
        print("✓ EXERCISE CATALOG SEEDING COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_exercise_catalog())
