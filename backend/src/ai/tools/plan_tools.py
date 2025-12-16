"""Function tools for fitness plan generation and orchestration.

These tools enable the conversation agent to orchestrate plan generation
by calling specialist agents via function tools.
"""

import json
from contextvars import ContextVar
from datetime import date, datetime, timedelta
from uuid import UUID

from agents import Runner, function_tool
from pydantic import BaseModel, Field

from src.ai.app_agents.meal_phase_agent import meal_phase_agent
from src.ai.app_agents.workout_phase_agent import workout_phase_agent
from src.ai.schemas import MealPlanMetadata, WorkoutPlanMetadata
from src.services.plan_service import PlanService

# Context variables for passing user_id, db_session, and conversation_id to function tools
_user_id_context: ContextVar[UUID | None] = ContextVar("user_id", default=None)
_db_session_context: ContextVar[object | None] = ContextVar("db_session", default=None)
_conversation_id_context: ContextVar[UUID | None] = ContextVar("conversation_id", default=None)


def set_plan_tools_context(user_id: UUID, db_session: object, conversation_id: UUID | None = None) -> None:
    """Set the context for plan tools to enable database persistence.

    This should be called by the AI service before invoking agents that use
    the build_fitness_plan tool.

    Args:
        user_id: User's UUID for plan ownership
        db_session: Database session for persistence operations
        conversation_id: Optional conversation ID for plan message insertion
    """
    _user_id_context.set(user_id)
    _db_session_context.set(db_session)
    _conversation_id_context.set(conversation_id)


def clear_plan_tools_context() -> None:
    """Clear the plan tools context after agent execution.

    This ensures context doesn't leak between different user requests.
    """
    _user_id_context.set(None)
    _db_session_context.set(None)
    _conversation_id_context.set(None)


def _validate_and_parse_phases(phase_inputs: list) -> tuple[list[dict], date, date, int]:
    """Validate and parse phase dates into structured data.

    Args:
        phase_inputs: List of PhaseInput objects with name, start_date, end_date

    Returns:
        Tuple of (phase_data, plan_start_date, plan_end_date, total_duration_weeks)

    Raises:
        ValueError: If phase dates are invalid or inconsistent
    """
    if not phase_inputs:
        raise ValueError("At least one phase is required.")

    phase_data = []
    for idx, phase_input in enumerate(phase_inputs, 1):
        try:
            phase_start = datetime.strptime(phase_input.start_date, "%Y-%m-%d").date()
            phase_end = datetime.strptime(phase_input.end_date, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(
                f"Invalid date format in phase {idx} ('{phase_input.name}'). Use YYYY-MM-DD."
            ) from e

        # Validate phase dates
        if phase_end <= phase_start:
            raise ValueError(
                f"Phase {idx} ('{phase_input.name}'): end_date must be after start_date."
            )

        # Calculate phase duration
        phase_days = (phase_end - phase_start).days
        phase_weeks = (phase_days + 6) // 7  # Round up

        if phase_weeks < 2:
            raise ValueError(
                f"Phase {idx} ('{phase_input.name}'): duration too short ({phase_weeks} weeks). Minimum 2 weeks."
            )
        if phase_weeks > 16:
            raise ValueError(
                f"Phase {idx} ('{phase_input.name}'): duration too long ({phase_weeks} weeks). Maximum 16 weeks."
            )

        phase_data.append({
            "name": phase_input.name,
            "start_date": phase_start,
            "end_date": phase_end,
            "duration_weeks": phase_weeks,
        })

    # Validate phase continuity (each phase should start when previous ends)
    for i in range(1, len(phase_data)):
        prev_end = phase_data[i - 1]["end_date"]
        curr_start = phase_data[i]["start_date"]
        # Allow a gap of 0-1 days (same day or next day)
        gap_days = (curr_start - prev_end).days
        if gap_days < 0:
            raise ValueError(
                f"Phase overlap detected: '{phase_data[i-1]['name']}' ends {prev_end.isoformat()} but '{phase_data[i]['name']}' starts {curr_start.isoformat()}."
            )
        if gap_days > 1:
            raise ValueError(
                f"Phase gap detected: '{phase_data[i-1]['name']}' ends {prev_end.isoformat()} but '{phase_data[i]['name']}' starts {curr_start.isoformat()} ({gap_days} day gap)."
            )

    # Calculate total plan duration from phases
    # Plan start = first phase start, Plan end = last phase end
    start_date = phase_data[0]["start_date"]
    end_date = phase_data[-1]["end_date"]
    total_days = (end_date - start_date).days
    actual_duration_weeks = (total_days + 6) // 7  # Round up

    # Validate total duration
    if actual_duration_weeks < 4:
        raise ValueError(
            f"Total plan duration too short: {actual_duration_weeks} weeks. Minimum 4 weeks required."
        )
    if actual_duration_weeks > 52:
        raise ValueError(
            f"Total plan duration too long: {actual_duration_weeks} weeks. Maximum 52 weeks allowed."
        )

    return phase_data, start_date, end_date, actual_duration_weeks


def _get_conversation_id() -> UUID | None:
    """Get the conversation ID from context."""
    return _conversation_id_context.get()


async def _build_phase_with_agents(
    phase_info: dict,
    phase_num: int,
    total_phases: int,
    requirements,  # FitnessPlanInput
):
    """Build a single phase by calling workout and meal agents.

    Args:
        phase_info: Dict with name, start_date, end_date, duration_weeks
        phase_num: Current phase number (1-indexed)
        total_phases: Total number of phases in plan
        requirements: FitnessPlanInput with user requirements

    Returns:
        PhaseOutput with workout and meal details
    """
    from src.ai.schemas import PhaseOutput

    phase_name = phase_info["name"]
    phase_start = phase_info["start_date"]
    phase_end = phase_info["end_date"]
    phase_weeks = phase_info["duration_weeks"]

    # Determine phase-specific objectives
    phase_objectives = _get_phase_objectives(
        phase_name, requirements.primary_goal, phase_num, total_phases
    )

    # Build phase-specific workout details
    workout_phase_prompt = f"""Generate workout details for this phase:

Phase Context:
- Phase {phase_num} of {total_phases}: {phase_name}
- Duration: {phase_weeks} weeks ({phase_start.isoformat()} to {phase_end.isoformat()})
- Objectives: {', '.join(phase_objectives)}

Overall Workout Plan:
{requirements.workout_plan.description}

User Context:
- Fitness Level: {requirements.workout_plan.fitness_level}
- Workout Frequency: {requirements.workout_plan.workout_frequency} days/week
- Equipment: {requirements.workout_plan.equipment_access}
- Time per Session: {requirements.workout_plan.time_per_session} minutes
- Injuries/Conditions: {', '.join(requirements.workout_plan.injuries_or_conditions) if requirements.workout_plan.injuries_or_conditions else 'None'}

Generate the specific workout cycle, intensity guidance, volume notes, and progression strategy for this phase."""

    workout_details_result = await Runner.run(
        starting_agent=workout_phase_agent,
        input=workout_phase_prompt,
        session=None,
    )
    workout_details = workout_details_result.final_output

    # Build phase-specific meal details
    # Calculate day of week for phase start to help with scheduling
    phase_start_day = phase_start.strftime('%A')  # e.g., 'Monday', 'Tuesday'
    
    meal_phase_prompt = f"""Generate meal details for this phase:

Phase Context:
- Phase {phase_num} of {total_phases}: {phase_name}
- Duration: {phase_weeks} weeks ({phase_start.isoformat()} to {phase_end.isoformat()})
- Phase Starts On: {phase_start_day}, {phase_start.isoformat()}
- Objectives: {', '.join(phase_objectives)}

Overall Meal Plan:
{requirements.meal_plan.description}

User Context:
- Dietary Restrictions: {', '.join(requirements.meal_plan.dietary_restrictions) if requirements.meal_plan.dietary_restrictions else 'None'}
- Meal Frequency: {requirements.meal_plan.meal_frequency} meals/day
- Primary Goal: {requirements.primary_goal}

Generate the specific calorie target, macro split, sample meal plans, and nutrition focus for this phase."""

    meal_details_result = await Runner.run(
        starting_agent=meal_phase_agent,
        input=meal_phase_prompt,
        session=None,
    )
    meal_details = meal_details_result.final_output

    # Create phase output
    return PhaseOutput(
        phase_number=phase_num,
        name=phase_name,
        objectives=phase_objectives,
        start_date=phase_start.isoformat(),
        end_date=phase_end.isoformat(),
        duration_weeks=phase_weeks,
        workout_details=workout_details,
        meal_details=meal_details,
    )


async def _save_plan_to_database(
    fitness_plan_output,  # FitnessPlanOutput
    requirements,  # FitnessPlanInput
    start_date: date,
) -> str:
    """Save fitness plan to database and add conversation message.

    Args:
        fitness_plan_output: FitnessPlanOutput to save
        requirements: FitnessPlanInput with user requirements
        start_date: Plan start date

    Returns:
        Plan ID string (UUID or error message)
    """
    user_id = _user_id_context.get()
    db_session = _db_session_context.get()

    if not user_id or not db_session:
        return "pending_save_no_context"

    try:
        from datetime import datetime as dt

        from src.services.conversation_service import ConversationService
        from src.services.plan_service import PlanService

        # Create plan service
        plan_service = PlanService(db_session)

        # Prepare requirements dict from nested structure
        requirements_dict = {
            "name": requirements.name,
            "description": requirements.description,
            "primary_goal": requirements.primary_goal,
            "workout_plan": {
                "fitness_level": requirements.workout_plan.fitness_level,
                "workout_frequency": requirements.workout_plan.workout_frequency,
                "equipment_access": requirements.workout_plan.equipment_access,
                "time_per_session": requirements.workout_plan.time_per_session,
                "injuries_or_conditions": requirements.workout_plan.injuries_or_conditions,
                "description": requirements.workout_plan.description,
                "schedule_preferences": requirements.workout_plan.schedule_preferences.model_dump() if requirements.workout_plan.schedule_preferences else None,
            },
            "meal_plan": {
                "dietary_restrictions": requirements.meal_plan.dietary_restrictions,
                "meal_frequency": requirements.meal_plan.meal_frequency,
                "description": requirements.meal_plan.description,
                "schedule_preferences": requirements.meal_plan.schedule_preferences.model_dump() if requirements.meal_plan.schedule_preferences else None,
            },
        }

        # Create fitness plan record with parsed dates
        start_datetime = dt.combine(start_date, dt.min.time())

        fitness_plan = await plan_service.create_plan(
            user_id=user_id,
            goal=requirements.primary_goal,
            requirements=requirements_dict,
            duration_weeks=fitness_plan_output.duration_weeks,
            start_date=start_datetime,
        )

        # Prepare plan output with requirements included
        plan_output_dict = fitness_plan_output.model_dump()
        plan_output_dict["requirements"] = requirements_dict

        # Save the complete generated plan data
        await plan_service.save_generated_plan(
            plan_id=fitness_plan.id,
            plan_output=plan_output_dict,
        )

        # Insert a plan message into the conversation for rich display
        conversation_id = _get_conversation_id()
        if conversation_id:
            conv_service = ConversationService(db_session)
            await conv_service.add_message(
                conversation_id=conversation_id,
                sender_type="plan",
                message_content=f"Fitness Plan Created: {fitness_plan_output.duration_weeks}-week plan",
                plan_id=fitness_plan.id,
            )

        return str(fitness_plan.id)

    except Exception as save_error:
        print(f"Warning: Failed to save plan to database: {save_error}")
        return f"not_saved_{save_error}"


def _parse_and_validate_dates(
    start_date_str: str, end_date_str: str | None, duration_weeks: int
) -> tuple[date, date, int]:
    """Parse and validate start/end dates for a fitness plan.

    Args:
        start_date_str: Start date as "YYYY-MM-DD" or "today"
        end_date_str: Optional end date as "YYYY-MM-DD" or None
        duration_weeks: Fallback duration if no end_date provided

    Returns:
        Tuple of (start_date, end_date, actual_duration_weeks)

    Raises:
        ValueError: If dates are invalid or inconsistent
    """
    # Parse start date
    if start_date_str.lower() == "today":
        start = date.today()
    else:
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(
                f"Invalid start_date format: '{start_date_str}'. Use YYYY-MM-DD or 'today'."
            ) from e

    # Calculate or parse end date
    if end_date_str:
        try:
            end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(
                f"Invalid end_date format: '{end_date_str}'. Use YYYY-MM-DD."
            ) from e

        # Calculate actual duration from dates
        days_diff = (end - start).days
        if days_diff <= 0:
            raise ValueError(f"end_date ({end_date_str}) must be after start_date ({start_date_str}).")

        # Calculate weeks (round up to ensure full coverage)
        actual_weeks = (days_diff + 6) // 7  # Round up

        if actual_weeks < 4:
            raise ValueError(
                f"Plan duration too short: {actual_weeks} weeks. Minimum 4 weeks required."
            )
        if actual_weeks > 52:
            raise ValueError(
                f"Plan duration too long: {actual_weeks} weeks. Maximum 52 weeks allowed."
            )
    else:
        # Use duration_weeks to calculate end date
        if not (4 <= duration_weeks <= 52):
            raise ValueError(
                f"duration_weeks must be between 4 and 52. Got: {duration_weeks}"
            )
        actual_weeks = duration_weeks
        end = start + timedelta(weeks=duration_weeks)

    return start, end, actual_weeks


class WorkoutSchedulePreferences(BaseModel):
    """Scheduling preferences specific to workout training."""
    
    model_config = {"extra": "forbid"}
    
    split_type: str = Field(
        default="weekly_fixed",
        description="Training split type: 'weekly_fixed' (same days each week) or 'rolling' (e.g., 4-day cycle repeats regardless of calendar week)",
    )
    preferred_workout_days: list[str] | None = Field(
        default=None,
        description="Preferred days for workouts (e.g., ['Monday', 'Wednesday', 'Friday', 'Saturday']) for weekly_fixed. Leave None for rolling splits.",
    )
    rest_days: list[str] | None = Field(
        default=None,
        description="Mandatory rest days (e.g., ['Sunday']) for weekly_fixed schedules",
    )
    preferred_time: str | None = Field(
        default=None,
        description="Preferred workout time: 'morning' (6-10am), 'afternoon' (12-4pm), 'evening' (5-9pm), or specific time like '6:00 AM'",
    )
    notes: str | None = Field(
        default=None, 
        description="Additional workout scheduling notes or constraints"
    )


class MealSchedulePreferences(BaseModel):
    """Scheduling preferences for meal prep and grocery shopping."""
    
    model_config = {"extra": "forbid"}
    
    preferred_grocery_day: str | None = Field(
        default=None,
        description="Preferred day for grocery shopping (e.g., 'Sunday', 'Saturday morning')"
    )
    grocery_frequency: str = Field(
        default="weekly",
        description="Grocery shopping frequency: 'weekly', 'biweekly', 'custom'"
    )
    preferred_meal_prep_day: str | None = Field(
        default=None,
        description="Preferred day for batch meal prep (e.g., 'Sunday', 'Wednesday evening')"
    )
    meal_prep_frequency: str = Field(
        default="weekly",
        description="Meal prep frequency: 'weekly', 'twice_weekly', 'custom'"
    )
    notes: str | None = Field(
        default=None,
        description="Additional meal/grocery scheduling notes or constraints"
    )


class WorkoutPlanInput(BaseModel):
    """Complete workout plan data including metadata, requirements, and scheduling."""
    
    model_config = {"extra": "forbid"}
    
    # Workout requirements
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
    
    # High-level workout strategy
    description: str = Field(
        description="High-level workout plan strategy spanning all phases. Include: program type (e.g., 'Push/Pull/Legs'), progression strategy, key training principles, equipment usage, and how intensity/volume/frequency changes across phases."
    )
    
    # Structured metadata
    metadata: WorkoutPlanMetadata = Field(
        description="Structured workout metadata with program_type, progression_strategy, training_principles, equipment_used, and phase_progression_notes"
    )
    
    # Workout-specific scheduling
    schedule_preferences: WorkoutSchedulePreferences = Field(
        default_factory=WorkoutSchedulePreferences,
        description="Scheduling preferences specific to workout training"
    )


class MealPlanInput(BaseModel):
    """Complete meal plan data including metadata, requirements, and scheduling."""
    
    model_config = {"extra": "forbid"}
    
    # Nutrition requirements
    dietary_restrictions: list[str] = Field(
        default_factory=list, description="Dietary restrictions like vegetarian, vegan, gluten_free"
    )
    meal_frequency: int = Field(default=3, description="Number of meals per day", ge=3, le=6)
    
    # High-level nutrition strategy
    description: str = Field(
        description="High-level nutrition strategy spanning all phases. Include: dietary approach, macro distribution strategy, calorie targets per phase, meal timing preferences, and how nutrition adjusts as phases progress."
    )
    
    # Structured metadata
    metadata: MealPlanMetadata = Field(
        description="Structured meal metadata with dietary_approach, macro_strategy, meal_timing, hydration_guidance, and phase_nutrition_notes"
    )
    
    # Meal/prep/grocery-specific scheduling
    schedule_preferences: MealSchedulePreferences = Field(
        default_factory=MealSchedulePreferences,
        description="Scheduling preferences for meal prep and grocery shopping"
    )


class PhaseInput(BaseModel):
    """Input for a single phase with explicit dates."""

    model_config = {"extra": "forbid"}

    name: str = Field(description="Phase name (e.g., 'Foundation Phase', 'Building Phase', 'Peak Performance')")
    start_date: str = Field(description="Phase start date in YYYY-MM-DD format")
    end_date: str = Field(description="Phase end date in YYYY-MM-DD format")


class FitnessPlanInput(BaseModel):
    """Input parameters for complete fitness plan generation.
    
    A fitness plan contains:
    - Basic plan information (name, goal, description)
    - Phases with explicit dates
    - A workout plan (with its own requirements, metadata, and schedule preferences)
    - A meal plan (with its own requirements, metadata, and schedule preferences)
    """

    model_config = {"extra": "forbid"}

    # Plan-level basic information
    name: str = Field(
        description="Plan name (e.g., '12-Week Muscle Building Program', 'Summer Shred Plan', '2026 Marathon Training')"
    )
    primary_goal: str = Field(
        description="Primary fitness goal (e.g., 'muscle_gain', 'weight_loss', 'strength_building', 'marathon_training')"
    )
    description: str = Field(
        description="Overall plan description and context (2-3 sentences describing the complete program)"
    )
    
    # Phase structure with explicit dates
    phases: list[PhaseInput] = Field(
        description="List of phases with explicit start and end dates. Each phase MUST have: name, start_date (YYYY-MM-DD), and end_date (YYYY-MM-DD). The first phase's start_date is the plan start date. The last phase's end_date is the plan end date. Phases should be contiguous with no gaps. IMPORTANT: Always use explicit dates in YYYY-MM-DD format. Examples: [{name: 'Foundation Phase', start_date: '2025-12-15', end_date: '2026-01-11'}, {name: 'Progression Phase', start_date: '2026-01-12', end_date: '2026-02-08'}]",
        min_length=1
    )
    
    # Workout plan (complete with metadata and scheduling)
    workout_plan: WorkoutPlanInput = Field(
        description="Complete workout plan including requirements, high-level strategy, metadata, and workout-specific scheduling preferences"
    )
    
    # Meal plan (complete with metadata and scheduling)
    meal_plan: MealPlanInput = Field(
        description="Complete meal plan including requirements, high-level nutrition strategy, metadata, and meal/prep/grocery scheduling preferences"
    )
    
    # Plan-level avoided dates (applies to both workouts and meals)
    avoid_dates: list[str] | None = Field(
        default=None,
        description="Specific dates to avoid for ALL activities (e.g., ['2025-12-25', '2026-01-01'] for holidays, travel). Format: YYYY-MM-DD"
    )


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
        from src.ai.schemas import FitnessPlanOutput

        # 1. Validate and parse phase dates
        phase_data, start_date, end_date, actual_duration_weeks = _validate_and_parse_phases(
            requirements.phases
        )
        num_phases = len(phase_data)

        # 2. Build phases using phase-specific agents
        phases = []
        for phase_num, phase_info in enumerate(phase_data, 1):
            phase_output = await _build_phase_with_agents(
                phase_info, phase_num, num_phases, requirements
            )
            phases.append(phase_output)

        # 3. Create comprehensive multi-phase fitness plan output
        # Generate key principles from workout and meal metadata
        key_principles = []
        if requirements.workout_plan.metadata.training_principles:
            key_principles.extend(requirements.workout_plan.metadata.training_principles[:3])  # Top 3 training principles
        if requirements.meal_plan.metadata.dietary_approach:
            key_principles.append(f"Nutrition: {requirements.meal_plan.metadata.dietary_approach}")
        
        # Generate success metrics based on goal and plan structure
        success_metrics = [
            f"Complete all {actual_duration_weeks} weeks of training",
            f"Progress through all {num_phases} phase(s) successfully",
            "Track workouts and nutrition consistently",
            f"Achieve {requirements.primary_goal} objective",
        ]

        fitness_plan_output = FitnessPlanOutput(
            goal_summary=f"{requirements.name}: {requirements.description}",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            duration_weeks=actual_duration_weeks,
            fitness_level=requirements.workout_plan.fitness_level,
            workout_metadata=requirements.workout_plan.metadata,
            meal_metadata=requirements.meal_plan.metadata,
            phases=phases,
            key_principles=key_principles,
            success_metrics=success_metrics,
            important_notes=f"This {actual_duration_weeks}-week plan runs from {start_date.isoformat()} to {end_date.isoformat()} and is designed for {requirements.workout_plan.fitness_level} level with {num_phases} phase(s). Each phase has specific objectives and will transition automatically. Adjust weights and intensity based on your progress. Listen to your body and take extra rest if needed.",
        )

        # Validate plan completeness
        fitness_plan_output.validate_completeness()

        # 4. Save plan to database
        plan_id = await _save_plan_to_database(fitness_plan_output, requirements, start_date)

        # 5. Return result
        return json.dumps({
            "fitness_plan": fitness_plan_output.model_dump(),
            "status": "success",
            "message": f"Successfully created a {fitness_plan_output.duration_weeks}-week fitness plan for {requirements.primary_goal} with {num_phases} phase(s)!",
            "plan_id": plan_id,
        }, indent=2)

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

        # Build comprehensive plan details from normalized tables
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

        # Add training plan details from workout_plans table
        if active_plan.workout_plans and len(active_plan.workout_plans) > 0:
            workout_plan = active_plan.workout_plans[0]
            plan_details["training_plan"] = {
                "frequency_per_week": workout_plan.frequency_per_week,
                "progression_strategy": workout_plan.progression_strategy,
                "program_type": workout_plan.program_type,
                "training_principles": workout_plan.training_principles,
            }

        # Add nutrition plan details from meal_plans table
        if active_plan.meal_plans and len(active_plan.meal_plans) > 0:
            meal_plan = active_plan.meal_plans[0]
            plan_details["nutrition_plan"] = {
                "daily_calorie_target": meal_plan.daily_calorie_target,
                "protein_grams": meal_plan.protein_grams_target,
                "carbs_grams": meal_plan.carbs_grams_target,
                "fats_grams": meal_plan.fats_grams_target,
                "meals_per_day": meal_plan.meals_per_day,
            }

        # Add phase information from phases table
        if active_plan.phases and len(active_plan.phases) > 0:
            plan_details["phases"] = [
                {
                    "phase_number": phase.phase_number,
                    "name": phase.name,
                    "objectives": phase.objectives,
                    "start_date": phase.start_date.isoformat() if phase.start_date else None,
                    "end_date": phase.end_date.isoformat() if phase.end_date else None,
                }
                for phase in active_plan.phases
            ]

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
