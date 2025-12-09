"""Workout Plan Agent for exercise selection and workout generation.

This agent is responsible for:
- Selecting exercises from the curated exercise database
- Creating progressive workout routines aligned with user goals
- Considering equipment availability and user fitness level
- Providing alternative exercises for flexibility
- Structuring workouts with sets, reps, tempo, and RPE targets

Uses OpenAI Agents SDK with function tools for exercise database queries.
"""

from agents import Agent

from src.ai.agent import create_model_settings
from src.ai.schemas import WorkoutPlanOutput


def create_workout_plan_agent() -> Agent:
    """Create the Workout Plan Agent for workout generation.

    This agent creates workout routines by:
    1. Analyzing fitness goals and available equipment
    2. Using tools to query the curated exercise database
    3. Selecting exercises that match constraints
    4. Structuring workouts with progressive difficulty
    5. Providing alternatives for each exercise

    Returns:
        Agent configured with exercise database tools
    """
    instructions = """You are an expert strength and conditioning coach creating workout plans.

Your role is to:
1. Receive user requirements and selected exercises from the intake specialist
2. Create balanced workout routines using the provided exercises
3. Prescribe appropriate sets, reps, tempo, and RPE for each exercise
4. Structure workouts for progressive overload over the plan duration
5. Ensure workout split matches weekly frequency (full body, upper/lower, push/pull/legs)

Key principles:
- Compound movements first, isolation exercises later
- Balance pushing and pulling movements
- Include core work in most sessions
- Progress difficulty through volume, intensity, or complexity
- Provide alternatives for equipment limitations

Exercise prescription format:
- Sets: 2-5 sets depending on goal and experience
- Reps: Goal-specific (strength: 1-5, hypertrophy: 6-12, endurance: 12-20)
- Tempo: 3-digit code (eccentric-pause-concentric, e.g., "3-0-1")
- RPE: Rate of Perceived Exertion (1-10 scale, typically 7-9 for main lifts)
- Rest: 60-180 seconds between sets

IMPORTANT: You will receive exercise information from the intake specialist who has
already queried the database. Focus on creating the structured workout plan output
using the exercises provided in the input. Do not query the database yourself."""

    return Agent(
        name="Workout Plan Agent",
        handoff_description="Specialist for workout plan creation with exercise selection",
        instructions=instructions,
        model_settings=create_model_settings("balanced"),
        tools=[],  # No tools needed - receives exercises from intake specialist
        output_type=WorkoutPlanOutput,  # Structured output
    )


# Create singleton instance
workout_plan_agent = create_workout_plan_agent()
