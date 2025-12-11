"""Workout API endpoints."""
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.api.deps import CurrentUserId, DatabaseSession
from src.integrations.exercise_database import get_alternative_exercises
from src.models.workout import Workout
from src.schemas import create_success_response

router = APIRouter()


@router.get("/{workout_id}")
async def get_workout(
    workout_id: UUID,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get workout details.

    Args:
        workout_id: UUID of the workout
        db: Database session
        current_user: Authenticated user

    Returns:
        Workout details

    Raises:
        HTTPException: If workout not found
    """
    stmt = select(Workout).where(Workout.id == workout_id)
    result = await db.execute(stmt)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    return create_success_response({
        "id": str(workout.id),
        "name": workout.name,
        "workout_type": workout.workout_type,
        "duration_minutes": workout.duration_minutes,
        "intensity_level": workout.intensity_level,
        "workout_structure": workout.workout_structure,
    })


@router.get("/{workout_id}/alternatives")
async def get_workout_alternatives(
    workout_id: UUID,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get alternative exercises for a workout.

    This endpoint analyzes each exercise in a workout and suggests alternatives
    that target the same muscle groups with similar or easier difficulty levels.

    Args:
        workout_id: UUID of the workout
        db: Database session
        current_user: Authenticated user

    Returns:
        List of exercise alternatives for each exercise in the workout

    Raises:
        HTTPException: If workout not found
    """
    # Get the workout
    stmt = select(Workout).where(Workout.id == workout_id)
    result = await db.execute(stmt)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Extract exercises from workout details
    workout_details = workout.workout_details or {}
    exercises = workout_details.get("exercises", [])

    if not exercises:
        return create_success_response({
            "workout_id": str(workout_id),
            "workout_name": workout.name,
            "alternatives": [],
            "message": "No exercises found in this workout",
        })

    # Get alternatives for each exercise
    alternatives_list = []
    for exercise in exercises:
        exercise_name = exercise.get("name", "")
        if not exercise_name:
            continue

        # Get alternatives from exercise database
        alts = get_alternative_exercises(exercise_name)

        # Format alternatives with reasoning
        formatted_alts = []
        for alt in alts[:3]:  # Limit to top 3 alternatives
            # Determine difficulty comparison
            original_diff = exercise.get("difficulty", "intermediate")
            alt_diff = alt.get("difficulty", "intermediate")

            diff_levels = {"beginner": 1, "intermediate": 2, "advanced": 3}
            original_level = diff_levels.get(original_diff, 2)
            alt_level = diff_levels.get(alt_diff, 2)

            if alt_level < original_level:
                difficulty_comparison = "easier"
                reason = f"Same muscle groups, {difficulty_comparison}"
            elif alt_level > original_level:
                difficulty_comparison = "harder"
                reason = f"Same muscle groups, {difficulty_comparison}"
            else:
                difficulty_comparison = "similar"
                reason = "Same muscle groups and difficulty"

            # Add equipment difference if significant
            if alt.get("equipment") == "bodyweight" and exercise.get("equipment") != "bodyweight":
                reason = "Bodyweight alternative"

            formatted_alts.append({
                "id": str(alt.get("id", "")),
                "name": alt.get("name", ""),
                "reason": reason,
                "difficulty": difficulty_comparison,
                "equipment": alt.get("equipment", ""),
                "muscle_groups": alt.get("muscle_groups", []),
            })

        alternatives_list.append({
            "exercise_id": exercise.get("id", ""),
            "original_exercise": exercise_name,
            "original_sets": exercise.get("sets"),
            "original_reps": exercise.get("reps"),
            "original_equipment": exercise.get("equipment", ""),
            "alternatives": formatted_alts,
        })

    return create_success_response({
        "workout_id": str(workout_id),
        "workout_name": workout.name,
        "alternatives": alternatives_list,
    })
