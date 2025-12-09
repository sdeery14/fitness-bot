"""Workout planning tools using exercise database.

These tools wrap the exercise database functions for use by AI agents.
All tools return JSON strings as required by OpenAI Agents SDK.
"""
import asyncio
import json

from agents import function_tool
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.integrations import exercise_database
from src.models.workout import Exercise, Workout

# Load sentence transformer model for semantic search
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _embedding_model


@function_tool
def get_exercises_by_muscle_group(muscle_group: str) -> str:
    """Find exercises targeting a specific muscle group.

    Args:
        muscle_group: Target muscle (chest, back, legs, shoulders, arms, core)

    Returns:
        JSON string with list of exercises including name, equipment, difficulty
    """
    exercises = exercise_database.get_exercises_by_muscle_group(muscle_group)
    return json.dumps(exercises, indent=2)


@function_tool
def get_exercises_by_equipment(equipment: str) -> str:
    """Find exercises that can be performed with specific equipment.

    Args:
        equipment: Available equipment (barbell, dumbbell, bodyweight, machine, cable, band)

    Returns:
        JSON string with list of exercises using that equipment
    """
    exercises = exercise_database.get_exercises_by_equipment(equipment)
    return json.dumps(exercises, indent=2)


@function_tool
def get_exercises_by_difficulty(difficulty: str) -> str:
    """Find exercises matching a difficulty level.

    Args:
        difficulty: Fitness level (beginner, intermediate, advanced)

    Returns:
        JSON string with list of exercises at that difficulty
    """
    exercises = exercise_database.get_exercises_by_difficulty(difficulty)
    return json.dumps(exercises, indent=2)


@function_tool
def get_alternative_exercises(exercise_name: str) -> str:
    """Find alternative exercises for a given exercise.

    Alternatives target the same muscle groups and have similar difficulty.

    Args:
        exercise_name: Name of the exercise to find alternatives for

    Returns:
        JSON string with list of alternative exercises
    """
    alternatives = exercise_database.get_alternative_exercises(exercise_name)
    return json.dumps(alternatives, indent=2)


@function_tool
def suggest_alternatives(
    workout_id: str,
    reason: str,
    user_constraints: str = None,
) -> str:
    """Suggest alternative exercises for a workout based on user constraints.

    Use this when a user wants to modify their workout due to equipment limitations,
    injury, difficulty level, or personal preference.

    Args:
        workout_id: UUID of the workout to modify
        reason: Why alternatives are needed (e.g., 'no equipment', 'knee injury', 'too difficult')
        user_constraints: Optional specific constraints (e.g., 'only bodyweight', 'low impact')

    Returns:
        JSON string with suggested alternatives for each exercise in the workout
    """
    from uuid import UUID
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models.workout import Workout
    import asyncio

    async def _get_alternatives():
        async with AsyncSessionLocal() as db:
            stmt = select(Workout).where(Workout.id == UUID(workout_id))
            result = await db.execute(stmt)
            workout = result.scalar_one_or_none()

            if not workout:
                return {"error": f"Workout {workout_id} not found"}

            alternatives_list = []
            workout_details = workout.workout_details or {}
            exercises = workout_details.get("exercises", [])

            for exercise in exercises:
                exercise_name = exercise.get("name", "")
                # Get alternatives from exercise database
                alts = exercise_database.get_alternative_exercises(exercise_name)

                # Filter based on reason
                filtered_alts = []
                for alt in alts:
                    if reason.lower() in ["no equipment", "bodyweight only"]:
                        if alt.get("equipment", "").lower() == "bodyweight":
                            filtered_alts.append(alt)
                    elif "injury" in reason.lower() or "low impact" in reason.lower():
                        if alt.get("difficulty", "").lower() in ["beginner", "intermediate"]:
                            filtered_alts.append(alt)
                    elif "too difficult" in reason.lower():
                        if alt.get("difficulty", "").lower() == "beginner":
                            filtered_alts.append(alt)
                    else:
                        filtered_alts.append(alt)

                alternatives_list.append({
                    "original_exercise": exercise_name,
                    "original_sets": exercise.get("sets"),
                    "original_reps": exercise.get("reps"),
                    "alternatives": filtered_alts[:3],  # Top 3 alternatives
                    "reason": reason,
                })

            return {
                "workout_id": workout_id,
                "workout_name": workout.name,
                "alternatives": alternatives_list,
                "recommendation": f"Suggested {len(alternatives_list)} exercise alternatives based on: {reason}",
            }

    result = asyncio.run(_get_alternatives())
    return json.dumps(result, indent=2)


@function_tool
def modify_intensity(
    workout_id: str,
    intensity_change: str,
    percentage: int = 20,
) -> str:
    """Modify the intensity of a workout by adjusting sets, reps, or weights.

    Args:
        workout_id: UUID of the workout to modify
        intensity_change: Direction to adjust ('increase' or 'decrease')
        percentage: Percentage to adjust by (default 20%)

    Returns:
        JSON string with modified workout parameters
    """
    from uuid import UUID
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models.workout import Workout
    import asyncio

    async def _modify():
        async with AsyncSessionLocal() as db:
            stmt = select(Workout).where(Workout.id == UUID(workout_id))
            result = await db.execute(stmt)
            workout = result.scalar_one_or_none()

            if not workout:
                return {"error": f"Workout {workout_id} not found"}

            workout_details = workout.workout_details or {}
            exercises = workout_details.get("exercises", [])
            modifier = 1 + (percentage / 100) if intensity_change == "increase" else 1 - (percentage / 100)

            modified_exercises = []
            for exercise in exercises:
                modified = exercise.copy()
                # Adjust reps and sets
                if "reps" in modified:
                    original_reps = modified["reps"]
                    modified["reps"] = max(1, int(original_reps * modifier))
                if "sets" in modified:
                    original_sets = modified["sets"]
                    modified["sets"] = max(1, int(original_sets * modifier))
                # Suggest weight adjustment
                if "weight_kg" in modified:
                    original_weight = modified["weight_kg"]
                    modified["weight_kg"] = round(original_weight * modifier, 1)

                modified_exercises.append(modified)

            return {
                "workout_id": workout_id,
                "workout_name": workout.name,
                "intensity_change": intensity_change,
                "percentage_adjusted": percentage,
                "original_exercises": exercises,
                "modified_exercises": modified_exercises,
                "notes": f"Intensity {intensity_change}d by {percentage}%. Adjust as needed based on your energy level.",
            }

    result = asyncio.run(_modify())
    return json.dumps(result, indent=2)


@function_tool
def adjust_frequency(
    workout_name: str,
    current_weekly_frequency: int,
    desired_frequency: int,
    reason: str = None,
) -> str:
    """Adjust how often a workout should be performed per week.

    Args:
        workout_name: Name of the workout type (e.g., 'Upper Body', 'Cardio')
        current_weekly_frequency: Current times per week
        desired_frequency: Target times per week
        reason: Optional reason for adjustment (e.g., 'recovery', 'plateau', 'time constraints')

    Returns:
        JSON string with frequency adjustment recommendation
    """
    frequency_diff = desired_frequency - current_weekly_frequency

    if frequency_diff > 0:
        recommendation = f"Increase {workout_name} from {current_weekly_frequency}x to {desired_frequency}x per week"
        tips = [
            "Gradually add sessions over 2-3 weeks to allow adaptation",
            "Ensure adequate rest between sessions (24-48 hours)",
            "Monitor fatigue and recovery",
            "Consider reducing intensity when adding frequency",
        ]
    elif frequency_diff < 0:
        recommendation = f"Decrease {workout_name} from {current_weekly_frequency}x to {desired_frequency}x per week"
        tips = [
            "Prioritize quality over quantity in remaining sessions",
            "Consider increasing intensity to maintain progress",
            "Use extra time for recovery or other activities",
            "Monitor if reduced frequency still meets your goals",
        ]
    else:
        recommendation = f"Maintain current frequency of {current_weekly_frequency}x per week"
        tips = ["Current frequency appears optimal", "Continue monitoring progress"]

    return json.dumps({
        "workout_name": workout_name,
        "current_frequency": current_weekly_frequency,
        "desired_frequency": desired_frequency,
        "frequency_change": frequency_diff,
        "recommendation": recommendation,
        "implementation_tips": tips,
        "reason": reason or "User preference",
    }, indent=2)


@function_tool
def search_exercises_by_description(
    description: str,
    limit: int = 5,
    equipment_filter: str = None,
    difficulty_filter: str = None,
) -> str:
    """Search exercises by semantic meaning using natural language description.

    This uses RAG (Retrieval Augmented Generation) with pgvector to find exercises
    that match the semantic meaning of the description, not just keyword matching.

    Examples:
    - "exercises that strengthen my lower back"
    - "movements for explosive power"
    - "stretches for shoulder mobility"
    - "core stability exercises"

    Args:
        description: Natural language description of what you're looking for
        limit: Maximum number of results to return (default 5)
        equipment_filter: Optional equipment constraint (e.g., 'bodyweight', 'dumbbells')
        difficulty_filter: Optional difficulty level (beginner, intermediate, advanced)

    Returns:
        JSON string with list of exercises ranked by semantic similarity
    """
    import asyncio
    from sqlalchemy import select, text
    from src.database import async_session_factory
    from src.models.workout import Exercise

    async def _search():
        # Generate embedding for the search description
        model = get_embedding_model()
        query_embedding = model.encode(description, convert_to_numpy=True).tolist()

        async with async_session_factory() as session:
            # Build the SQL query with vector similarity search
            # Using cosine distance for similarity (<=> operator in pgvector)
            query_parts = [
                "SELECT e.id, e.name, e.exercise_type, e.target_muscle_groups,",
                "       e.equipment_required, e.instructions, e.form_cues,",
                "       e.difficulty, e.sets, e.reps, e.rest_seconds,",
                "       (e.embedding <=> :query_embedding) AS distance",
                "FROM exercises e",
                "WHERE e.embedding IS NOT NULL",
            ]

            params = {"query_embedding": str(query_embedding)}

            # Add filters if specified
            if equipment_filter:
                query_parts.append("  AND :equipment = ANY(e.equipment_required)")
                params["equipment"] = equipment_filter

            if difficulty_filter:
                query_parts.append("  AND e.difficulty = :difficulty")
                params["difficulty"] = difficulty_filter

            # Order by similarity and limit results
            query_parts.append("ORDER BY distance ASC")
            query_parts.append("LIMIT :limit")
            params["limit"] = limit

            sql_query = "\n".join(query_parts)

            # Execute the query
            result = await session.execute(text(sql_query), params)
            rows = result.fetchall()

            # Format results
            exercises = []
            for row in rows:
                exercises.append({
                    "id": str(row.id),
                    "name": row.name,
                    "exercise_type": row.exercise_type,
                    "target_muscle_groups": row.target_muscle_groups,
                    "equipment_required": row.equipment_required,
                    "difficulty": row.difficulty,
                    "instructions": row.instructions,
                    "form_cues": row.form_cues,
                    "prescription": {
                        "sets": row.sets,
                        "reps": row.reps,
                        "rest_seconds": row.rest_seconds,
                    },
                    "similarity_score": float(1 - row.distance),  # Convert distance to similarity
                })

            return {
                "search_description": description,
                "results_count": len(exercises),
                "filters_applied": {
                    "equipment": equipment_filter,
                    "difficulty": difficulty_filter,
                },
                "exercises": exercises,
            }

    result = asyncio.run(_search())
    return json.dumps(result, indent=2)


@function_tool
def find_similar_exercises(
    exercise_name: str,
    limit: int = 3,
) -> str:
    """Find exercises similar to a given exercise using semantic similarity.

    Uses the exercise's embedding to find other exercises with similar movement
    patterns, muscle groups, or training effects.

    Args:
        exercise_name: Name of the reference exercise
        limit: Maximum number of similar exercises to return (default 3)

    Returns:
        JSON string with list of similar exercises
    """
    import asyncio
    from sqlalchemy import select, text
    from src.database import async_session_factory
    from src.models.workout import Exercise

    async def _find_similar():
        async with async_session_factory() as session:
            # First, get the reference exercise
            result = await session.execute(
                select(Exercise).where(Exercise.name == exercise_name)
            )
            reference_exercise = result.scalar_one_or_none()

            if not reference_exercise:
                return {
                    "error": f"Exercise '{exercise_name}' not found in database"
                }

            if reference_exercise.embedding is None:
                return {
                    "error": f"Exercise '{exercise_name}' does not have an embedding"
                }

            # Find similar exercises using vector similarity
            sql_query = """
                SELECT e.id, e.name, e.exercise_type, e.target_muscle_groups,
                       e.equipment_required, e.instructions, e.difficulty,
                       (e.embedding <=> :reference_embedding) AS distance
                FROM exercises e
                WHERE e.embedding IS NOT NULL
                  AND e.name != :reference_name
                ORDER BY distance ASC
                LIMIT :limit
            """

            result = await session.execute(
                text(sql_query),
                {
                    "reference_embedding": str(reference_exercise.embedding),
                    "reference_name": exercise_name,
                    "limit": limit,
                }
            )
            rows = result.fetchall()

            similar_exercises = []
            for row in rows:
                similar_exercises.append({
                    "id": str(row.id),
                    "name": row.name,
                    "exercise_type": row.exercise_type,
                    "target_muscle_groups": row.target_muscle_groups,
                    "equipment_required": row.equipment_required,
                    "difficulty": row.difficulty,
                    "instructions": row.instructions,
                    "similarity_score": float(1 - row.distance),
                })

            return {
                "reference_exercise": exercise_name,
                "similar_exercises": similar_exercises,
                "count": len(similar_exercises),
            }

    result = asyncio.run(_find_similar())
    return json.dumps(result, indent=2)
