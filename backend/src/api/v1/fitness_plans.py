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
    plan_snapshot: dict | None = None


class UpdatePlanRequest(BaseModel):
    """Plan update request."""

    current_status: str | None = None
    plan_snapshot: dict | None = None


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
            "plan_snapshot": plan.plan_snapshot or {},
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
                "plan_snapshot": plan.plan_snapshot,
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
            "plan_snapshot": plan.plan_snapshot,
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

    return create_success_response({
        "id": str(plan.id),
        "user_id": str(plan.user_id),
        "goal_description": plan.goal_description,
        "goal_type": plan.goal_type,
        "duration_weeks": plan.duration_weeks,
        "start_date": plan.start_date.isoformat(),
        "target_end_date": plan.end_date.isoformat(),
        "current_status": plan.status,
        "plan_snapshot": plan.plan_snapshot,
        "created_at": plan.created_at.isoformat(),
        "updated_at": plan.updated_at.isoformat(),
    })


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

    # Update plan_snapshot if provided
    if request.plan_snapshot is not None:
        plan.plan_snapshot = {**(plan.plan_snapshot or {}), **request.plan_snapshot}
        await db.commit()
        await db.refresh(plan)

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
        "plan_snapshot": plan.plan_snapshot,
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
