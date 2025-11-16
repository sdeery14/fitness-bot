"""Fitness plan endpoints."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.api.deps import CurrentUserId, DatabaseSession
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

    goal: str
    requirements: dict
    duration_weeks: int = 12


class UpdatePlanRequest(BaseModel):
    """Plan update request."""

    status: str | None = None
    requirements: dict | None = None


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    request: CreatePlanRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> PlanResponse:
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
    plan_service = PlanService(db)

    try:
        plan = await plan_service.create_plan(
            user_id=user_id,
            goal=request.goal,
            requirements=request.requirements,
            duration_weeks=request.duration_weeks,
        )

        return PlanResponse(
            id=str(plan.id),
            user_id=str(plan.user_id),
            goal=plan.goal,
            duration_weeks=plan.duration_weeks,
            requirements=plan.requirements,
            status=plan.status,
            created_at=plan.created_at.isoformat(),
            completed_at=plan.completed_at.isoformat() if plan.completed_at else None,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> PlanResponse:
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
    plan_service = PlanService(db)
    plan = await plan_service.get_plan(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    # Verify ownership
    if plan.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this plan",
        )

    return PlanResponse(
        id=str(plan.id),
        user_id=str(plan.user_id),
        goal=plan.goal,
        duration_weeks=plan.duration_weeks,
        requirements=plan.requirements,
        status=plan.status,
        created_at=plan.created_at.isoformat(),
        completed_at=plan.completed_at.isoformat() if plan.completed_at else None,
    )


@router.get("/active", response_model=PlanResponse | None)
async def get_active_plan(
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> PlanResponse | None:
    """Get user's active fitness plan.

    Args:
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Active plan if exists, None otherwise
    """
    plan_service = PlanService(db)
    plans = await plan_service.get_user_plans(user_id, limit=1)

    if not plans:
        return None

    plan = plans[0]
    return PlanResponse(
        id=str(plan.id),
        user_id=str(plan.user_id),
        goal=plan.goal,
        duration_weeks=plan.duration_weeks,
        requirements=plan.requirements,
        status=plan.status,
        created_at=plan.created_at.isoformat(),
        completed_at=plan.completed_at.isoformat() if plan.completed_at else None,
    )


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    request: UpdatePlanRequest,
    user_id: CurrentUserId,
    db: DatabaseSession,
) -> PlanResponse:
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
    plan_service = PlanService(db)
    plan = await plan_service.get_plan(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    # Verify ownership
    if plan.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this plan",
        )

    # Update status if provided
    if request.status is not None:
        plan = await plan_service.update_plan_status(
            plan_id=plan_id,
            status=request.status,
        )

    # Update requirements if provided
    if request.requirements is not None:
        plan.requirements = {**plan.requirements, **request.requirements}
        await db.commit()
        await db.refresh(plan)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found after update",
        )

    return PlanResponse(
        id=str(plan.id),
        user_id=str(plan.user_id),
        goal=plan.goal,
        duration_weeks=plan.duration_weeks,
        requirements=plan.requirements,
        status=plan.status,
        created_at=plan.created_at.isoformat(),
        completed_at=plan.completed_at.isoformat() if plan.completed_at else None,
    )
