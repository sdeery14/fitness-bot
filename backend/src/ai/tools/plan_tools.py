"""Function tools for fitness plan generation and orchestration.

These tools enable the conversation agent to orchestrate plan generation
by calling specialist agents via function tools.
"""
import json
from contextvars import ContextVar
from uuid import UUID

from agents import Runner, function_tool
from pydantic import BaseModel, Field

from src.ai.app_agents.fitness_plan_agent import create_fitness_plan_agent
from src.ai.app_agents.meal_plan_agent import meal_plan_agent
from src.ai.app_agents.workout_plan_agent import workout_plan_agent
from src.ai.schemas import FitnessPlanOutput

# Context variables for passing user_id and db_session to function tools
_user_id_context: ContextVar[UUID | None] = ContextVar("user_id", default=None)
_db_session_context: ContextVar[object | None] = ContextVar("db_session", default=None)


def set_plan_tools_context(user_id: UUID, db_session: object) -> None:
    """Set the context for plan tools to enable database persistence.

    This should be called by the AI service before invoking agents that use
    the build_fitness_plan tool.

    Args:
        user_id: User's UUID for plan ownership
        db_session: Database session for persistence operations
    """
    _user_id_context.set(user_id)
    _db_session_context.set(db_session)


def clear_plan_tools_context() -> None:
    """Clear the plan tools context after agent execution.

    This ensures context doesn't leak between different user requests.
    """
    _user_id_context.set(None)
    _db_session_context.set(None)


class WorkoutPlanInput(BaseModel):
    """Input parameters for workout plan generation."""
    
    model_config = {"extra": "forbid"}
    
    primary_goal: str = Field(description="Primary fitness goal (e.g., 'muscle_gain', 'weight_loss')")
    fitness_level: str = Field(description="Fitness level: beginner, intermediate, or advanced")
    workout_frequency: int = Field(description="Number of workout days per week", ge=2, le=7)
    equipment_access: str = Field(description="Available equipment: full_gym, home_gym, or bodyweight")
    time_per_session: int = Field(default=60, description="Time per workout in minutes", ge=20, le=120)
    injuries_or_conditions: list[str] = Field(default_factory=list, description="Any injuries or health conditions")


class MealPlanInput(BaseModel):
    """Input parameters for meal plan generation."""
    
    model_config = {"extra": "forbid"}
    
    primary_goal: str = Field(description="Primary fitness goal (e.g., 'muscle_gain', 'weight_loss', 'maintenance')")
    dietary_restrictions: list[str] = Field(default_factory=list, description="Dietary restrictions like vegetarian, vegan, gluten_free")
    meal_frequency: int = Field(default=3, description="Number of meals per day", ge=3, le=6)
    preferences: str = Field(default="", description="Additional dietary preferences")


class FitnessPlanInput(BaseModel):
    """Input parameters for complete fitness plan generation."""
    
    model_config = {"extra": "forbid"}
    
    primary_goal: str = Field(description="Primary fitness goal")
    fitness_level: str = Field(description="Fitness level: beginner, intermediate, or advanced")
    workout_frequency: int = Field(description="Workout days per week", ge=2, le=7)
    equipment_access: str = Field(description="Available equipment")
    time_per_session: int = Field(default=60, description="Time per workout in minutes", ge=20, le=120)
    dietary_restrictions: list[str] = Field(default_factory=list, description="Dietary restrictions")
    meal_frequency: int = Field(default=3, description="Meals per day", ge=3, le=6)
    injuries_or_conditions: list[str] = Field(default_factory=list, description="Injuries or health conditions")


@function_tool
async def build_workout_plan(requirements: WorkoutPlanInput) -> str:
    """Build a workout plan using the Workout Plan Agent.

    This function tool calls the Workout Plan Agent with user requirements
    and returns a structured workout plan as JSON.

    Args:
        requirements: WorkoutPlanInput with all required parameters

    Returns:
        JSON string with WorkoutPlanOutput structure

    Raises:
        ValueError: If agent fails to generate plan
    """
    # Build prompt for workout agent
    prompt = f"""Create a workout plan with the following requirements:

Goal: {requirements.primary_goal}
Fitness Level: {requirements.fitness_level}
Frequency: {requirements.workout_frequency} days per week
Equipment: {requirements.equipment_access}
Time per session: {requirements.time_per_session} minutes
"""

    if requirements.injuries_or_conditions:
        prompt += f"\nInjuries/Conditions to consider: {', '.join(requirements.injuries_or_conditions)}"

    # Run workout plan agent with structured output
    result = await Runner.run(
        starting_agent=workout_plan_agent,
        input=prompt,
        session=None,
    )

    # Extract structured output and return as JSON string
    if hasattr(result, "output_data") and result.output_data:
        return json.dumps(result.output_data.model_dump(), indent=2)

    raise ValueError("Workout Plan Agent did not return structured output")


@function_tool
async def build_meal_plan(requirements: MealPlanInput) -> str:
    """Build a meal plan using the Meal Plan Agent.

    This function tool calls the Meal Plan Agent with user requirements
    and returns a structured meal plan as JSON.

    Args:
        requirements: MealPlanInput with all required parameters

    Returns:
        JSON string with MealPlanOutput structure

    Raises:
        ValueError: If agent fails to generate plan
    """
    # Build prompt for meal agent
    prompt = f"""Create a meal plan with the following requirements:

Goal: {requirements.primary_goal}
Meal Frequency: {requirements.meal_frequency} meals per day
"""

    if requirements.dietary_restrictions:
        prompt += f"\nDietary Restrictions: {', '.join(requirements.dietary_restrictions)}"

    if requirements.preferences:
        prompt += f"\nPreferences: {requirements.preferences}"

    # Run meal plan agent with structured output
    result = await Runner.run(
        starting_agent=meal_plan_agent,
        input=prompt,
        session=None,
    )

    # Extract structured output and return as JSON string
    if hasattr(result, "output_data") and result.output_data:
        return json.dumps(result.output_data.model_dump(), indent=2)

    raise ValueError("Meal Plan Agent did not return structured output")


@function_tool
async def build_fitness_plan(requirements: FitnessPlanInput) -> str:
    """Build a complete fitness plan by orchestrating workout and meal plan agents.

    This is the main function tool that the conversation agent calls when ready
    to generate a complete fitness plan. It coordinates the specialist agents
    and returns a structured plan as JSON.

    The user_id and db_session are retrieved from context variables set by the
    AI service before invoking the agent.

    Args:
        requirements: FitnessPlanInput with all required parameters

    Returns:
        JSON string containing:
            - fitness_plan: FitnessPlanOutput (structured plan data)
            - status: str ("success" or "error")
            - message: str (human-readable result message)
            - plan_id: str (database ID once saved)

    Raises:
        ValueError: If agents fail to generate plan
    """
    try:
        # Create fitness plan agent (it will use build_workout_plan and build_meal_plan tools)
        fitness_agent = create_fitness_plan_agent(workout_plan_agent, meal_plan_agent)

        # Build prompt from requirements
        prompt = f"""Create a complete fitness plan for a user with these requirements:

Primary Goal: {requirements.primary_goal}
Fitness Level: {requirements.fitness_level}
Workout Frequency: {requirements.workout_frequency} days per week
Equipment Access: {requirements.equipment_access}
Time per Session: {requirements.time_per_session} minutes
"""

        if requirements.dietary_restrictions:
            prompt += f"Dietary Restrictions: {', '.join(requirements.dietary_restrictions)}\n"

        if requirements.injuries_or_conditions:
            prompt += f"Injuries/Conditions: {', '.join(requirements.injuries_or_conditions)}\n"

        # Run fitness plan agent - it will call build_workout_plan and build_meal_plan internally
        result = await Runner.run(
            starting_agent=fitness_agent,
            input=prompt,
            session=None,
        )

        # Extract structured output
        if not (hasattr(result, "output_data") and result.output_data):
            raise ValueError("Fitness Plan Agent did not return structured output")

        fitness_plan_output: FitnessPlanOutput = result.output_data

        # Validate plan completeness
        fitness_plan_output.validate_completeness()

        # Get user_id and db_session from context
        user_id = _user_id_context.get()
        db_session = _db_session_context.get()

        # Save plan to database if user_id and db_session are available
        plan_id = "pending_save"
        if user_id and db_session:
            try:
                from src.services.plan_service import PlanService

                # Create plan service
                plan_service = PlanService(db_session)

                # Create fitness plan record
                fitness_plan = await plan_service.create_plan(
                    user_id=user_id,
                    goal=requirements.primary_goal,
                    requirements={
                        "fitness_level": requirements.fitness_level,
                        "workout_frequency": requirements.workout_frequency,
                        "equipment_access": requirements.equipment_access,
                        "time_per_session": requirements.time_per_session,
                        "dietary_restrictions": requirements.dietary_restrictions,
                        "meal_frequency": requirements.meal_frequency,
                        "injuries_or_conditions": requirements.injuries_or_conditions,
                    },
                    duration_weeks=fitness_plan_output.duration_weeks,
                )

                # Save the complete generated plan data
                await plan_service.save_generated_plan(
                    plan_id=fitness_plan.id,
                    plan_output=fitness_plan_output.model_dump(),
                )

                plan_id = str(fitness_plan.id)

            except Exception as save_error:
                # Log the error but don't fail the entire operation
                # The plan was generated successfully, we just couldn't save it
                print(f"Warning: Failed to save plan to database: {save_error}")
                plan_id = f"not_saved_{save_error}"

        result_dict = {
            "fitness_plan": fitness_plan_output.model_dump(),
            "status": "success",
            "message": f"Successfully created a {fitness_plan_output.duration_weeks}-week fitness plan for {requirements.primary_goal}!",
            "plan_id": plan_id,
        }

        return json.dumps(result_dict, indent=2)

    except Exception as e:
        error_dict = {
            "status": "error",
            "message": f"Failed to generate fitness plan: {str(e)}",
            "error_details": str(e),
        }
        return json.dumps(error_dict, indent=2)
