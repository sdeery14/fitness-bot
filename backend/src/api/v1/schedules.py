"""Schedule endpoints for daily workout and meal tracking."""
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUserId, DatabaseSession
from src.schemas import create_error_response, create_success_response
from src.schemas.schedule import (
    ScheduleEntryComplete,
    ScheduleEntryRead,
    ScheduleEntrySkip,
    TodayScheduleResponse,
    UpcomingScheduleResponse,
)
from src.services.schedule_service import ScheduleService

router = APIRouter()


@router.get("/plan/{plan_id}")
async def get_schedule_by_plan(
    plan_id: UUID,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get schedule for a specific fitness plan.

    Returns the schedule and all entries for the given plan.

    Args:
        plan_id: Fitness plan UUID
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Schedule with entries and statistics
    """
    from src.services.plan_service import PlanService

    # Verify plan belongs to user
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

    if plan.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                code="FORBIDDEN",
                message="You don't have permission to access this plan's schedule"
            )
        )

    service = ScheduleService(db)
    schedule = await service.get_schedule_by_plan(fitness_plan_id=plan_id)

    if not schedule:
        return create_success_response({
            "schedule": None,
            "message": "No schedule found for this plan"
        })

    # Calculate statistics
    total_entries = len(schedule.entries)
    completed_count = sum(1 for e in schedule.entries if e.completion_status == "completed")
    scheduled_count = sum(1 for e in schedule.entries if e.completion_status == "scheduled")
    skipped_count = sum(1 for e in schedule.entries if e.completion_status == "skipped")
    workout_count = sum(1 for e in schedule.entries if e.entry_type == "workout")
    meal_count = sum(1 for e in schedule.entries if e.entry_type == "meal")

    # Get upcoming entries (next 7 days)
    today = date.today()
    upcoming_entries = [
        {
            "id": str(e.id),
            "entry_type": e.entry_type,
            "entry_date": e.entry_date.isoformat(),
            "entry_time": e.entry_time.isoformat() if e.entry_time else None,
            "completion_status": e.completion_status,
            "workout_name": e.workout.name if e.workout else None,
            "meal_name": e.meal.name if e.meal else None,
        }
        for e in schedule.entries
        if e.entry_date >= today and e.entry_date <= today + timedelta(days=7)
    ][:20]  # Limit to 20 upcoming

    return create_success_response({
        "schedule_id": str(schedule.id),
        "start_date": schedule.start_date.isoformat(),
        "last_recalculated_at": schedule.last_recalculated_at.isoformat(),
        "statistics": {
            "total_entries": total_entries,
            "completed": completed_count,
            "scheduled": scheduled_count,
            "skipped": skipped_count,
            "total_workouts": workout_count,
            "total_meals": meal_count,
            "completion_rate": round(completed_count / total_entries * 100, 1) if total_entries > 0 else 0,
        },
        "upcoming_entries": upcoming_entries,
    })


@router.get("/today", response_model=TodayScheduleResponse)
async def get_today_schedule(
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get today's schedule for the current user.

    Returns all scheduled workouts and meals for today with their completion status.

    Args:
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Today's schedule with entries and summary stats
    """
    service = ScheduleService(db)
    entries = await service.get_today_schedule(user_id=user_id)

    # Calculate summary stats
    total_workouts = sum(1 for e in entries if e.entry_type == "workout")
    total_meals = sum(1 for e in entries if e.entry_type == "meal")
    completed_count = sum(1 for e in entries if e.completion_status == "completed")
    scheduled_count = sum(1 for e in entries if e.completion_status == "scheduled")

    # Convert to response schemas
    entry_reads = [
        ScheduleEntryRead(
            id=e.id,
            schedule_id=e.schedule_id,
            entry_type=e.entry_type,
            entry_date=e.entry_date,
            entry_time=e.entry_time,
            completion_status=e.completion_status,
            completed_at=e.completed_at,
            workout_id=e.workout_id,
            meal_id=e.meal_id,
            workout_name=e.workout.name if e.workout else None,
            meal_name=e.meal.name if e.meal else None,
            user_notes=e.user_notes,
            skipped_reason=e.skipped_reason,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in entries
    ]

    return TodayScheduleResponse(
        date=date.today(),
        entries=entry_reads,
        summary={
            "total_workouts": total_workouts,
            "total_meals": total_meals,
            "completed_count": completed_count,
            "scheduled_count": scheduled_count,
        },
    )


@router.get("/upcoming", response_model=UpcomingScheduleResponse)
async def get_upcoming_schedule(
    user_id: CurrentUserId,
    db: DatabaseSession,
    days: int = 14,
):
    """Get upcoming schedule for the next N days.

    Returns scheduled activities for the specified number of days ahead.

    Args:
        days: Number of days to look ahead (1-30, default 14)
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Upcoming schedule grouped by date
    """
    service = ScheduleService(db)
    entries = await service.get_upcoming_schedule(user_id=user_id, days=days)

    # Group entries by date
    grouped_by_date: dict[str, list[ScheduleEntryRead]] = {}
    for e in entries:
        date_key = e.entry_date.isoformat()
        if date_key not in grouped_by_date:
            grouped_by_date[date_key] = []

        grouped_by_date[date_key].append(
            ScheduleEntryRead(
                id=e.id,
                schedule_id=e.schedule_id,
                entry_type=e.entry_type,
                entry_date=e.entry_date,
                entry_time=e.entry_time,
                completion_status=e.completion_status,
                completed_at=e.completed_at,
                workout_id=e.workout_id,
                meal_id=e.meal_id,
                grocery_list=e.grocery_list,
                prep_instructions=e.prep_instructions,
                workout_name=e.workout.name if e.workout else None,
                meal_name=e.meal.name if e.meal else None,
                user_notes=e.user_notes,
                skipped_reason=e.skipped_reason,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
        )

    # Convert all entries
    entry_reads = [
        ScheduleEntryRead(
            id=e.id,
            schedule_id=e.schedule_id,
            entry_type=e.entry_type,
            entry_date=e.entry_date,
            entry_time=e.entry_time,
            completion_status=e.completion_status,
            completed_at=e.completed_at,
            workout_id=e.workout_id,
            meal_id=e.meal_id,
            grocery_list=e.grocery_list,
            prep_instructions=e.prep_instructions,
            workout_name=e.workout.name if e.workout else None,
            meal_name=e.meal.name if e.meal else None,
            user_notes=e.user_notes,
            skipped_reason=e.skipped_reason,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in entries
    ]

    return UpcomingScheduleResponse(
        start_date=date.today(),
        end_date=date.today(),  # Will be calculated from entries
        entries=entry_reads,
        grouped_by_date=grouped_by_date,
    )


@router.post("/entries/{entry_id}/complete")
async def mark_entry_complete(
    entry_id: UUID,
    request: ScheduleEntryComplete,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Mark a schedule entry as completed.

    Updates the entry's completion status and records the completion time.

    Args:
        entry_id: Schedule entry UUID
        request: Completion details (optional user notes)
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Success response with updated entry

    Raises:
        HTTPException: If entry not found or user doesn't have permission
    """
    service = ScheduleService(db)

    try:
        entry = await service.mark_entry_complete(
            entry_id=entry_id,
            user_notes=request.user_notes,
        )

        # Verify the entry belongs to the current user
        # (check via schedule -> user_id relationship)
        if entry.schedule.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    code="FORBIDDEN",
                    message="You don't have permission to modify this entry",
                ),
            )

        return create_success_response(
            data={
                "id": str(entry.id),
                "entry_type": entry.entry_type,
                "completion_status": entry.completion_status,
                "completed_at": entry.completed_at.isoformat() if entry.completed_at else None,
                "message": f"{entry.entry_type.capitalize()} marked as complete!",
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(code="NOT_FOUND", message=str(e)),
        ) from e


@router.post("/entries/{entry_id}/skip")
async def mark_entry_skipped(
    entry_id: UUID,
    request: ScheduleEntrySkip,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Mark a schedule entry as skipped.

    Updates the entry's completion status to skipped with optional reason.

    Args:
        entry_id: Schedule entry UUID
        request: Skip details (optional reason)
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Success response with updated entry

    Raises:
        HTTPException: If entry not found or user doesn't have permission
    """
    service = ScheduleService(db)

    try:
        entry = await service.mark_entry_skipped(
            entry_id=entry_id,
            skipped_reason=request.skipped_reason,
        )

        # Verify the entry belongs to the current user
        if entry.schedule.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    code="FORBIDDEN",
                    message="You don't have permission to modify this entry",
                ),
            )

        return create_success_response(
            data={
                "id": str(entry.id),
                "entry_type": entry.entry_type,
                "completion_status": entry.completion_status,
                "skipped_reason": entry.skipped_reason,
                "message": f"{entry.entry_type.capitalize()} marked as skipped.",
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(code="NOT_FOUND", message=str(e)),
        ) from e

