"""Workout planning tools using exercise database.

These tools wrap the exercise database functions for use by AI agents.
All tools return JSON strings as required by OpenAI Agents SDK.
"""
import json

from agents import function_tool

from src.integrations import exercise_database


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
