"""Function tools for fitness plan generation and orchestration.

These tools enable the conversation agent to orchestrate plan generation
by calling specialist agents via function tools.
"""

import json
from contextvars import ContextVar
from uuid import UUID

from agents import Runner, function_tool
from pydantic import BaseModel, Field

from src.ai.app_agents.meal_plan_agent import meal_plan_agent
from src.ai.app_agents.workout_plan_agent import workout_plan_agent
from src.ai.schemas import SchedulePreferences
from src.services.plan_service import PlanService

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

    primary_goal: str = Field(
        description="Primary fitness goal (e.g., 'muscle_gain', 'weight_loss')"
    )
    fitness_level: str = Field(description="Fitness level: beginner, intermediate, or advanced")
    workout_frequency: int = Field(description="Number of workout days per week", ge=2, le=7)
    equipment_access: str = Field(
        description="Available equipment: full_gym, home_gym, or bodyweight"
    )
    time_per_session: int = Field(
        default=60, description="Time per workout in minutes", ge=20, le=120
    )
    injuries_or_conditions: list[str] = Field(
        default_factory=list, description="Any injuries or health conditions"
    )


class MealPlanInput(BaseModel):
    """Input parameters for meal plan generation."""

    model_config = {"extra": "forbid"}

    primary_goal: str = Field(
        description="Primary fitness goal (e.g., 'muscle_gain', 'weight_loss', 'maintenance')"
    )
    dietary_restrictions: list[str] = Field(
        default_factory=list, description="Dietary restrictions like vegetarian, vegan, gluten_free"
    )
    meal_frequency: int = Field(default=3, description="Number of meals per day", ge=3, le=6)
    preferences: str = Field(default="", description="Additional dietary preferences")


class FitnessPlanInput(BaseModel):
    """Input parameters for complete fitness plan generation."""

    model_config = {"extra": "forbid"}

    primary_goal: str = Field(description="Primary fitness goal")
    fitness_level: str = Field(description="Fitness level: beginner, intermediate, or advanced")
    workout_frequency: int = Field(description="Workout days per week", ge=2, le=7)
    equipment_access: str = Field(description="Available equipment")
    time_per_session: int = Field(
        default=60, description="Time per workout in minutes", ge=20, le=120
    )
    dietary_restrictions: list[str] = Field(
        default_factory=list, description="Dietary restrictions"
    )
    meal_frequency: int = Field(default=3, description="Meals per day", ge=3, le=6)
    injuries_or_conditions: list[str] = Field(
        default_factory=list, description="Injuries or health conditions"
    )
    duration_weeks: int = Field(
        default=12, description="Total program duration in weeks", ge=4, le=52
    )
    phases: list[str] | None = Field(
        default=None,
        description="Optional list of phase names/descriptions if user wants multi-phase plan (e.g., ['Bulk Phase - 8 weeks', 'Cut Phase - 4 weeks'] or ['Foundation - 6 weeks', 'Advanced - 6 weeks']). Leave None for single-phase plans."
    )
    schedule_preferences: SchedulePreferences = Field(
        default_factory=SchedulePreferences,
        description="User's scheduling preferences: split_type (weekly_fixed|rolling), preferred_workout_days, rest_days, preferred_time, avoid_dates, notes",
    )


async def build_workout_plan(requirements: WorkoutPlanInput) -> str:
    """Build a workout plan using the Workout Plan Agent.

    This function calls the Workout Plan Agent with user requirements
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
        prompt += (
            f"\nInjuries/Conditions to consider: {', '.join(requirements.injuries_or_conditions)}"
        )

    # Run workout plan agent with structured output
    result = await Runner.run(
        starting_agent=workout_plan_agent,
        input=prompt,
        session=None,
    )

    # Extract structured output from final_output
    # When agent has output_type defined, final_output contains the structured object
    if result.final_output:
        # final_output is of type WorkoutPlanOutput when workout_plan_agent has output_type=WorkoutPlanOutput
        return json.dumps(result.final_output.model_dump(), indent=2)

    raise ValueError("Workout Plan Agent did not return structured output")


async def build_meal_plan(requirements: MealPlanInput) -> str:
    """Build a meal plan using the Meal Plan Agent.

    This function calls the Meal Plan Agent with user requirements
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

    # Extract structured output from final_output
    # When agent has output_type defined, final_output contains the structured object
    if result.final_output:
        # final_output is of type MealPlanOutput when meal_plan_agent has output_type=MealPlanOutput
        return json.dumps(result.final_output.model_dump(), indent=2)

    raise ValueError("Meal Plan Agent did not return structured output")


@function_tool
async def build_fitness_plan(requirements: FitnessPlanInput) -> str:
    """Build a complete fitness plan with one or more phases.

    This is the main function tool that the conversation agent calls when ready
    to generate a complete fitness plan. It creates phases by calling workout
    and meal plan tools for each phase, then combines their results into a
    unified multi-phase fitness plan.

    The user_id and db_session are retrieved from context variables set by the
    AI service before invoking the agent.

    Args:
        requirements: FitnessPlanInput with all required parameters including
                     optional phases list for multi-phase plans

    Returns:
        JSON string containing:
            - fitness_plan: FitnessPlanOutput (structured plan data with phases)
            - status: str ("success" or "error")
            - message: str (human-readable result message)
            - plan_id: str (database ID once saved)

    Raises:
        ValueError: If plan generation fails
    """
    try:
        # Import schemas
        from src.ai.schemas import (
            FitnessPlanOutput,
            MealPlanOutput,
            PhaseOutput,
            WorkoutPlanOutput,
        )

        # Determine if multi-phase plan
        phase_descriptions = requirements.phases if requirements.phases else ["Complete Program"]
        num_phases = len(phase_descriptions)
        
        # Split duration across phases
        if num_phases == 1:
            phase_durations = [requirements.duration_weeks]
        else:
            # Distribute duration evenly across phases (AI can override later)
            weeks_per_phase = requirements.duration_weeks // num_phases
            remainder = requirements.duration_weeks % num_phases
            phase_durations = [weeks_per_phase] * num_phases
            # Add remainder weeks to last phase
            phase_durations[-1] += remainder

        # Build phases
        phases = []
        for phase_num, (phase_desc, phase_weeks) in enumerate(zip(phase_descriptions, phase_durations), 1):
            # Parse phase description (format: "Phase Name - X weeks" or just "Phase Name")
            phase_name = phase_desc.split(" -")[0].strip() if " -" in phase_desc else phase_desc
            
            # Determine phase-specific adjustments
            phase_objectives = _get_phase_objectives(phase_name, requirements.primary_goal, phase_num, num_phases)
            
            # Build workout plan for this phase
            workout_input = WorkoutPlanInput(
                primary_goal=f"{requirements.primary_goal} - {phase_name}",
                fitness_level=requirements.fitness_level,
                workout_frequency=requirements.workout_frequency,
                equipment_access=requirements.equipment_access,
                time_per_session=requirements.time_per_session,
                injuries_or_conditions=requirements.injuries_or_conditions,
            )

            workout_plan_json = await build_workout_plan(workout_input)
            workout_plan_dict = json.loads(workout_plan_json)
            workout_plan_output = WorkoutPlanOutput(**workout_plan_dict)

            # Build meal plan for this phase
            meal_input = MealPlanInput(
                primary_goal=f"{requirements.primary_goal} - {phase_name}",
                dietary_restrictions=requirements.dietary_restrictions,
                meal_frequency=requirements.meal_frequency,
                preferences="",
            )

            meal_plan_json = await build_meal_plan(meal_input)
            meal_plan_dict = json.loads(meal_plan_json)
            meal_plan_output = MealPlanOutput(**meal_plan_dict)

            # Create phase output
            phase_output = PhaseOutput(
                phase_number=phase_num,
                name=phase_name,
                objectives=phase_objectives,
                duration_weeks=phase_weeks,
                workout_plan_output=workout_plan_output,
                meal_plan_output=meal_plan_output,
            )
            phases.append(phase_output)

        # Create comprehensive multi-phase fitness plan output
        phase_summary = " + ".join([f"{p.name} ({p.duration_weeks}w)" for p in phases])
        
        fitness_plan_output = FitnessPlanOutput(
            goal_summary=f"Complete {requirements.duration_weeks}-week fitness plan for {requirements.primary_goal} with {num_phases} phase(s): {phase_summary}",
            duration_weeks=requirements.duration_weeks,
            fitness_level=requirements.fitness_level,
            phases=phases,
            key_principles=[
                "Progressive overload: Gradually increase intensity over time",
                "Consistency: Follow the plan regularly for best results",
                "Recovery: Prioritize sleep (7-9 hours) and rest days",
                "Nutrition: Fuel your body according to the meal plan",
                "Adaptation: Adjust based on progress and how you feel",
                "Phase transitions: Each phase builds on the previous one",
            ],
            success_metrics=[
                "Track workout performance (weight, reps, or time improvements)",
                "Monitor body measurements weekly (weight, body fat, measurements)",
                "Assess energy levels and recovery quality",
                "Check adherence rate (aim for 80%+ consistency)",
                "Evaluate how you feel overall (mood, strength, confidence)",
            ],
            important_notes=f"This {requirements.duration_weeks}-week plan is designed for {requirements.fitness_level} level with {num_phases} phase(s). Each phase has specific objectives and will transition automatically. Adjust weights and intensity based on your progress. Listen to your body and take extra rest if needed.",
        )

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

                # Prepare requirements dict
                requirements_dict = {
                    "fitness_level": requirements.fitness_level,
                    "workout_frequency": requirements.workout_frequency,
                    "equipment_access": requirements.equipment_access,
                    "time_per_session": requirements.time_per_session,
                    "dietary_restrictions": requirements.dietary_restrictions,
                    "meal_frequency": requirements.meal_frequency,
                    "injuries_or_conditions": requirements.injuries_or_conditions,
                    "schedule_preferences": requirements.schedule_preferences.model_dump(),
                }

                # Create fitness plan record
                fitness_plan = await plan_service.create_plan(
                    user_id=user_id,
                    goal=requirements.primary_goal,
                    requirements=requirements_dict,
                    duration_weeks=fitness_plan_output.duration_weeks,
                )

                # Prepare plan output with requirements included
                plan_output_dict = fitness_plan_output.model_dump()
                plan_output_dict["requirements"] = requirements_dict

                # Save the complete generated plan data
                await plan_service.save_generated_plan(
                    plan_id=fitness_plan.id,
                    plan_output=plan_output_dict,
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
            "message": f"Successfully created a {fitness_plan_output.duration_weeks}-week fitness plan for {requirements.primary_goal} with {num_phases} phase(s)!",
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


def _get_phase_objectives(phase_name: str, primary_goal: str, phase_num: int, total_phases: int) -> list[str]:
    """Generate phase-specific objectives based on phase name and position.
    
    Args:
        phase_name: Name of the phase (e.g., "Bulk Phase", "Cut Phase")
        primary_goal: User's primary fitness goal
        phase_num: Current phase number (1-indexed)
        total_phases: Total number of phases
        
    Returns:
        List of objectives for this phase
    """
    phase_lower = phase_name.lower()
    
    # Common phase patterns
    if "bulk" in phase_lower or "mass" in phase_lower:
        return [
            "Build muscle mass through progressive overload",
            "Increase strength on compound movements",
            "Maintain caloric surplus for muscle growth",
        ]
    elif "cut" in phase_lower or "shred" in phase_lower or "lean" in phase_lower:
        return [
            "Maintain muscle while reducing body fat",
            "Achieve caloric deficit through nutrition",
            "Increase cardiovascular conditioning",
        ]
    elif "strength" in phase_lower or "power" in phase_lower:
        return [
            "Maximize strength on primary lifts",
            "Focus on low-rep, high-weight training",
            "Improve neuromuscular efficiency",
        ]
    elif "hypertrophy" in phase_lower:
        return [
            "Optimize muscle growth through volume training",
            "Focus on time under tension",
            "Target muscle groups with isolation work",
        ]
    elif "foundation" in phase_lower or "base" in phase_lower or phase_num == 1:
        return [
            "Build foundational movement patterns",
            "Establish consistent training habits",
            "Progress safely at appropriate intensity",
        ]
    elif "advanced" in phase_lower or phase_num == total_phases:
        return [
            "Push performance to new levels",
            "Apply progressive overload principles",
            f"Achieve {primary_goal} goal",
        ]
    else:
        # Generic objectives based on position
        return [
            f"Progress toward {primary_goal}",
            "Build on previous phase achievements",
            "Maintain consistency and form quality",
        ]


@function_tool
async def get_active_fitness_plan() -> str:
    """Get the user's current active fitness plan details.

    This function retrieves the complete active fitness plan for the current user,
    including all training details, nutrition information, phases, and progress.
    Use this tool when the user asks about their current plan, wants to discuss
    modifications, or needs information about their training schedule or meals.

    Returns:
        JSON string containing:
            - plan_id: str (database ID)
            - status: str ("success" or "error")
            - plan_details: dict (complete plan information if found)
                - goal: str (primary fitness goal)
                - duration_weeks: int (total plan duration)
                - start_date: str (when plan started)
                - end_date: str (target completion date)
                - current_phase: dict (active phase information)
                - training_plan: dict (workout schedule and exercises)
                - nutrition_plan: dict (meal plans and macros)
                - phases: list (all plan phases)
                - key_principles: list (important guidelines)
                - success_metrics: list (progress tracking metrics)
            - message: str (human-readable result message)

    Raises:
        ValueError: If user context is not set or plan not found
    """
    try:
        # Get user_id and db_session from context
        user_id = _user_id_context.get()
        db_session = _db_session_context.get()

        if not user_id or not db_session:
            error_dict = {
                "status": "error",
                "message": "User context not available. Cannot retrieve fitness plan.",
                "plan_details": None,
            }
            return json.dumps(error_dict, indent=2)

        # Create plan service
        plan_service = PlanService(db_session)

        # Get active fitness plan
        active_plan = await plan_service.get_active_plan(user_id)

        if not active_plan:
            no_plan_dict = {
                "status": "success",
                "message": "No active fitness plan found. User may want to create a new plan.",
                "plan_details": None,
                "has_active_plan": False,
            }
            return json.dumps(no_plan_dict, indent=2)

        # Extract plan details from plan_snapshot
        plan_snapshot = active_plan.plan_snapshot or {}

        # Build comprehensive plan details
        plan_details = {
            "plan_id": str(active_plan.id),
            "goal": active_plan.goal_description,
            "goal_type": active_plan.goal_type,
            "duration_weeks": active_plan.duration_weeks,
            "start_date": active_plan.start_date.isoformat() if active_plan.start_date else None,
            "end_date": active_plan.end_date.isoformat() if active_plan.end_date else None,
            "status": active_plan.status,
            "created_at": active_plan.created_at.isoformat(),
        }

        # Add training plan details if available
        if "workout_plan" in plan_snapshot:
            workout_plan = plan_snapshot["workout_plan"]
            plan_details["training_plan"] = {
                "program_type": workout_plan.get("program_type"),
                "frequency_per_week": workout_plan.get("frequency_per_week"),
                "duration_weeks": workout_plan.get("duration_weeks"),
                "progression_notes": workout_plan.get("progression_notes"),
                "workouts": workout_plan.get("workouts", []),
            }

        # Add nutrition plan details if available
        if "meal_plan" in plan_snapshot:
            meal_plan = plan_snapshot["meal_plan"]
            plan_details["nutrition_plan"] = {
                "daily_calorie_target": meal_plan.get("daily_calorie_target"),
                "macro_split": meal_plan.get("macro_split"),
                "meal_frequency": meal_plan.get("meal_frequency"),
                "dietary_guidelines": meal_plan.get("dietary_guidelines"),
                "hydration_guidance": meal_plan.get("hydration_guidance"),
                "sample_days": meal_plan.get("sample_days", []),
            }

        # Add phase information if available
        if "phases" in plan_snapshot:
            plan_details["phases"] = plan_snapshot["phases"]

        # Add key principles if available
        if "key_principles" in plan_snapshot:
            plan_details["key_principles"] = plan_snapshot["key_principles"]

        # Add success metrics if available
        if "success_metrics" in plan_snapshot:
            plan_details["success_metrics"] = plan_snapshot["success_metrics"]

        # Add important notes if available
        if "important_notes" in plan_snapshot:
            plan_details["important_notes"] = plan_snapshot["important_notes"]

        result_dict = {
            "status": "success",
            "message": f"Found active fitness plan: {active_plan.goal_description}",
            "plan_details": plan_details,
            "has_active_plan": True,
        }

        return json.dumps(result_dict, indent=2)

    except Exception as e:
        error_dict = {
            "status": "error",
            "message": f"Failed to retrieve active fitness plan: {str(e)}",
            "error_details": str(e),
            "plan_details": None,
        }
        return json.dumps(error_dict, indent=2)
