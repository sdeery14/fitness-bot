"""Fitness plan endpoints."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.api.deps import CurrentUserId, DatabaseSession
from src.schemas import create_success_response
from src.services.plan_service import PlanService

router = APIRouter()


class PlanResponse(BaseModel):
    """Fitness plan response."""

    id: str
    user_id: str
    goal: str
    duration_weeks: int
    requirements: dict
    status: str
    created_at: str
    completed_at: str | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class CreatePlanRequest(BaseModel):
    """Plan creation request."""

    goal_description: str
    goal_type: str
    duration_weeks: int = 12
    start_date: str | None = None


class UpdatePlanRequest(BaseModel):
    """Plan update request."""

    current_status: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_plan(
    request: CreatePlanRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Create a new fitness plan.

    Args:
        request: Plan creation data
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Created plan

    Raises:
        HTTPException: If creation fails
    """
    from src.schemas import create_error_response

    # Validate request fields
    if not request.goal_type or not request.goal_type.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                code="VALIDATION_ERROR",
                message="goal_type cannot be empty"
            )
        )
    
    if not request.goal_description or not request.goal_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                code="VALIDATION_ERROR",
                message="goal_description cannot be empty"
            )
        )
    
    if request.duration_weeks <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                code="VALIDATION_ERROR",
                message="duration_weeks must be greater than 0"
            )
        )
    
    plan_service = PlanService(db)

    try:
        # Check for active plan
        active_plan = await plan_service.get_active_plan(user_id)
        if active_plan:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=create_error_response(
                    code="CONFLICT",
                    message="User already has an active fitness plan"
                )
            )
        
        # Parse start_date if provided
        start_date_obj = None
        if request.start_date:
            if isinstance(request.start_date, str):
                start_date_obj = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
            else:
                start_date_obj = request.start_date

        plan = await plan_service.create_plan(
            user_id=user_id,
            goal=request.goal_type,
            requirements={"goal_description": request.goal_description},
            duration_weeks=request.duration_weeks,
            start_date=start_date_obj,
        )

        # Format dates - if time is midnight (00:00:00), return just the date part
        start_date_str = None
        if plan.start_date:
            if plan.start_date.time().replace(tzinfo=None) == datetime.min.time():
                start_date_str = plan.start_date.date().isoformat()
            else:
                start_date_str = plan.start_date.isoformat()

        target_end_date_str = None
        if plan.end_date:
            if plan.end_date.time().replace(tzinfo=None) == datetime.min.time():
                target_end_date_str = plan.end_date.date().isoformat()
            else:
                target_end_date_str = plan.end_date.isoformat()

        return create_success_response({
            "id": str(plan.id),
            "user_id": str(plan.user_id),
            "goal_description": plan.goal_description,
            "goal_type": plan.goal_type,
            "duration_weeks": plan.duration_weeks,
            "start_date": start_date_str,
            "target_end_date": target_end_date_str,
            "current_status": plan.status,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
        })

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("")
@router.get("/")
async def list_plans(
    user_id: CurrentUserId,
    db: DatabaseSession,
    limit: int = 100,
    offset: int = 0,
):
    """List all fitness plans for the current user.

    Args:
        user_id: Current authenticated user ID
        db: Database session
        limit: Maximum number of plans to return (default: 100)
        offset: Number of plans to skip (default: 0)

    Returns:
        List of all user's fitness plans ordered by creation date
    """
    plan_service = PlanService(db)

    try:
        plans = await plan_service.get_user_plans(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        plans_data = []
        for plan in plans:
            # Format dates
            start_date_str = None
            if plan.start_date:
                if plan.start_date.time().replace(tzinfo=None) == datetime.min.time():
                    start_date_str = plan.start_date.date().isoformat()
                else:
                    start_date_str = plan.start_date.isoformat()

            target_end_date_str = None
            if plan.end_date:
                if plan.end_date.time().replace(tzinfo=None) == datetime.min.time():
                    target_end_date_str = plan.end_date.date().isoformat()
                else:
                    target_end_date_str = plan.end_date.isoformat()

            plans_data.append({
                "id": str(plan.id),
                "user_id": str(plan.user_id),
                "goal_description": plan.goal_description,
                "goal_type": plan.goal_type,
                "duration_weeks": plan.duration_weeks,
                "start_date": start_date_str,
                "target_end_date": target_end_date_str,
                "current_status": plan.status,
                "created_at": plan.created_at.isoformat(),
                "updated_at": plan.updated_at.isoformat(),
            })

        return create_success_response({
            "plans": plans_data,
            "total": len(plans_data),
            "limit": limit,
            "offset": offset,
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve plans: {str(e)}"
        ) from e


@router.get("/active")
async def get_active_plan(
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get user's active fitness plan.

    Args:
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Active plan if exists

    Raises:
        HTTPException: 404 if no active plan found
    """
    plan_service = PlanService(db)

    try:
        # Get active plan (status = 'active')
        plan = await plan_service.get_active_plan(user_id)

        if not plan:
            from src.schemas import create_error_response
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    code="NOT_FOUND",
                    message="No active fitness plan found"
                )
            )

        # Format dates - if time is midnight (00:00:00), return just the date part
        start_date_str = None
        if plan.start_date:
            if plan.start_date.time().replace(tzinfo=None) == datetime.min.time():
                start_date_str = plan.start_date.date().isoformat()
            else:
                start_date_str = plan.start_date.isoformat()

        target_end_date_str = None
        if plan.end_date:
            if plan.end_date.time().replace(tzinfo=None) == datetime.min.time():
                target_end_date_str = plan.end_date.date().isoformat()
            else:
                target_end_date_str = plan.end_date.isoformat()

        return create_success_response({
            "id": str(plan.id),
            "user_id": str(plan.user_id),
            "goal_description": plan.goal_description,
            "goal_type": plan.goal_type,
            "duration_weeks": plan.duration_weeks,
            "start_date": start_date_str,
            "target_end_date": target_end_date_str,
            "current_status": plan.status,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active plan: {str(e)}"
        ) from e


@router.get("/{plan_id}")
async def get_plan(
    plan_id: UUID,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get a specific fitness plan.

    Args:
        plan_id: Plan UUID
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Plan details

    Raises:
        HTTPException: If plan not found or not owned by user
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from src.models.fitness_plan import FitnessPlan, Phase
    from src.models.workout import Workout, Exercise, WorkoutPlan
    from src.models.meal import Meal, MealPlan
    from src.schemas import create_error_response

    # Load plan with all related data
    stmt = (
        select(FitnessPlan)
        .where(FitnessPlan.id == plan_id)
        .options(
            selectinload(FitnessPlan.phases),
            selectinload(FitnessPlan.workout_plans),
            selectinload(FitnessPlan.meal_plans),
        )
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                code="NOT_FOUND",
                message=f"Fitness plan {plan_id} not found"
            )
        )

    # Verify ownership
    if plan.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this plan",
        )

    # Build the nested structure that frontend expects (similar to old plan_snapshot)
    phases_data = []
    
    for phase in sorted(plan.phases, key=lambda p: p.phase_number):
        # Get workouts for this phase
        workouts_stmt = (
            select(Workout)
            .where(Workout.phase_id == phase.id)
            .options(selectinload(Workout.exercises))
        )
        workouts_result = await db.execute(workouts_stmt)
        workouts = list(workouts_result.scalars().all())
        
        # Build workout details
        workout_details = {
            "workouts": [
                {
                    "day_name": workout.name,
                    "workout_type": workout.workout_type,
                    "duration_minutes": workout.duration_minutes,
                    "intensity_level": workout.intensity_level,
                    "focus": workout.workout_structure.get("focus", ""),
                    "warmup": workout.workout_structure.get("warmup", ""),
                    "cooldown": workout.workout_structure.get("cooldown", ""),
                    "exercises": [
                        {
                            "name": exercise.name,
                            "exercise_type": exercise.exercise_type,
                            "target_muscle_groups": exercise.target_muscle_groups,
                            "equipment_required": exercise.equipment_required,
                            "sets": exercise.sets,
                            "reps": exercise.reps,
                            "duration_seconds": exercise.duration_seconds,
                            "rest_seconds": exercise.rest_seconds,
                            "tempo": exercise.tempo,
                            "rpe_target": exercise.rpe_target,
                            "instructions": exercise.instructions,
                            "form_cues": exercise.form_cues,
                        }
                        for exercise in sorted(workout.exercises, key=lambda e: e.exercise_order)
                    ]
                }
                for workout in workouts
            ],
            "workout_cycle": phase.phase_details.get("workout_cycle", []) if phase.phase_details else [],
        }
        
        # Get meals for this phase
        meals_stmt = select(Meal).where(Meal.phase_id == phase.id)
        meals_result = await db.execute(meals_stmt)
        meals = list(meals_result.scalars().all())
        
        # Group meals by day
        meals_by_day = {}
        for meal in meals:
            day = meal.day_of_week
            if day not in meals_by_day:
                meals_by_day[day] = []
            meals_by_day[day].append(meal)
        
        # Build sample days
        sample_days = []
        for day_num in sorted(meals_by_day.keys()):
            day_meals = meals_by_day[day_num]
            sample_days.append({
                "day": day_num,
                "meals": [
                    {
                        "meal_name": meal.name,
                        "total_calories": meal.calories,
                        "foods": [
                            {
                                "name": ingredient["name"],
                                "portion": f"{ingredient['quantity']} {ingredient['unit']}",
                                "calories": ingredient.get("calories", 0),
                                "protein_g": ingredient.get("protein_grams", 0),
                                "carbs_g": ingredient.get("carbs_grams", 0),
                                "fat_g": ingredient.get("fats_grams", 0),
                            }
                            for ingredient in meal.meal_details.get("ingredients", [])
                        ] if meal.meal_details else []
                    }
                    for meal in day_meals
                ]
            })
        
        # Get meal plan for calorie target
        meal_plan = plan.meal_plans[0] if plan.meal_plans else None
        
        meal_details = {
            "sample_days": sample_days,
            "daily_calorie_target": meal_plan.daily_calorie_target if meal_plan else 2000,
            "macro_split": meal_plan.macronutrient_distribution.get("macro_split", "40/30/30") if meal_plan and meal_plan.macronutrient_distribution else "40% Carbs, 30% Protein, 30% Fat",
        }
        
        # Calculate phase duration
        phase_duration_weeks = phase.phase_details.get("duration_weeks", 0) if phase.phase_details else 0
        
        phases_data.append({
            "id": str(phase.id),
            "phase_number": phase.phase_number,
            "name": phase.name,
            "phase_name": phase.name,  # Keep for backward compatibility
            "start_date": phase.start_date.isoformat() if phase.start_date else None,
            "end_date": phase.end_date.isoformat() if phase.end_date else None,
            "duration_weeks": phase_duration_weeks,
            "description": ", ".join(phase.objectives) if phase.objectives else "",
            "objectives": phase.objectives,
            "phase_details": phase.phase_details or {},
            "workout_details": workout_details,
            "meal_details": meal_details,
        })
    
    # Get workout and meal plan metadata
    workout_plan = plan.workout_plans[0] if plan.workout_plans else None
    meal_plan = plan.meal_plans[0] if plan.meal_plans else None
    
    # Build workout metadata
    workout_metadata = None
    if workout_plan:
        workout_metadata = {
            "phase_progression_notes": workout_plan.phase_progression_notes,
            "equipment_used": workout_plan.equipment_used or [],
        }
    
    # Build meal metadata
    meal_metadata = None
    if meal_plan:
        meal_metadata = {
            "dietary_approach": meal_plan.dietary_approach,
            "macro_strategy": meal_plan.macro_strategy,
            "meal_timing": meal_plan.meal_timing,
            "hydration_guidance": meal_plan.hydration_guidance,
            "phase_nutrition_notes": meal_plan.phase_nutrition_notes,
        }
    
    # Build response matching frontend expectations
    response_data = {
        "id": str(plan.id),
        "user_id": str(plan.user_id),
        "goal_description": plan.goal_description,
        "goal_type": plan.goal_type,
        "duration_weeks": plan.duration_weeks,
        "start_date": plan.start_date.isoformat(),
        "target_end_date": plan.end_date.isoformat(),
        "current_status": plan.status,
        "created_at": plan.created_at.isoformat(),
        "updated_at": plan.updated_at.isoformat(),
        
        # Plan-level metadata
        "key_principles": plan.key_principles or [],
        "success_metrics": plan.success_metrics or [],
        "important_notes": plan.important_notes,
        
        # Structured plan data
        "phases": phases_data,
        "workout_frequency": workout_plan.frequency_per_week if workout_plan else 3,
        "daily_calorie_target": meal_plan.daily_calorie_target if meal_plan else 2000,
        
        # Workout and meal metadata
        "workout_metadata": workout_metadata,
        "meal_metadata": meal_metadata,
    }

    return create_success_response(response_data)


@router.patch("/{plan_id}")
async def update_plan(
    plan_id: UUID,
    request: UpdatePlanRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Update a fitness plan.

    Args:
        plan_id: Plan UUID
        request: Update data
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Updated plan

    Raises:
        HTTPException: If plan not found or not owned by user
    """
    from src.schemas import create_error_response

    plan_service = PlanService(db)
    plan = await plan_service.get_plan(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                code="NOT_FOUND",
                message=f"Fitness plan {plan_id} not found"
            )
        )

    # Verify ownership
    if plan.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this plan",
        )

    # Update status if provided
    if request.current_status is not None:
        plan = await plan_service.update_plan_status(
            plan_id=plan_id,
            status=request.current_status,
        )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                code="NOT_FOUND",
                message=f"Fitness plan {plan_id} not found after update"
            )
        )

    return create_success_response({
        "id": str(plan.id),
        "user_id": str(plan.user_id),
        "goal_description": plan.goal_description,
        "goal_type": plan.goal_type,
        "duration_weeks": plan.duration_weeks,
        "start_date": plan.start_date.isoformat(),
        "target_end_date": plan.end_date.isoformat(),
        "current_status": plan.status,

        "created_at": plan.created_at.isoformat(),
        "updated_at": plan.updated_at.isoformat(),
    })


@router.get("/{plan_id}/suggestions")
async def get_plan_suggestions(
    plan_id: UUID,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get AI-generated improvement suggestions for a fitness plan.

    This endpoint analyzes the user's progress and adherence patterns
    to generate personalized recommendations for plan improvements.

    Args:
        plan_id: Plan UUID
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Improvement recommendations with analysis summary

    Raises:
        HTTPException: If plan not found or not owned by user
    """
    from src.schemas import create_error_response

    plan_service = PlanService(db)
    plan = await plan_service.get_plan(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                code="NOT_FOUND",
                message=f"Fitness plan {plan_id} not found"
            )
        )

    # Verify ownership
    if plan.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this plan",
        )

    try:
        # Generate improvement recommendations based on progress
        recommendations = await plan_service.generate_improvement_recommendations(
            user_id=user_id,
            fitness_plan_id=plan_id,
        )

        return create_success_response(recommendations)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        ) from e
