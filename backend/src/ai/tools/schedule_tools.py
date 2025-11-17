"""Schedule management tools for AI agents.

These tools allow AI agents to query and modify user schedules.
All tools return JSON strings as required by OpenAI Agents SDK.
"""
import json
from datetime import date, datetime
from uuid import UUID

from agents import function_tool
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schedule import ScheduleEntry
from src.services.schedule_service import ScheduleService


@function_tool
async def get_today_schedule(user_id: str, db: AsyncSession) -> str:
    """Get the user's schedule for today.

    Args:
        user_id: User's UUID as string
        db: Database session (injected by agent context)

    Returns:
        JSON string with today's workouts and meals
    """
    service = ScheduleService(db)
    entries = await service.get_today_schedule(user_id=UUID(user_id))

    result = {
        "date": date.today().isoformat(),
        "entries": [
            {
                "id": str(entry.id),
                "type": entry.entry_type,
                "time": entry.entry_time.isoformat() if entry.entry_time else None,
                "status": entry.completion_status,
                "workout_name": entry.workout.name if entry.workout else None,
                "meal_name": entry.meal.name if entry.meal else None,
            }
            for entry in entries
        ],
    }

    return json.dumps(result, indent=2)


@function_tool
async def get_upcoming_schedule(user_id: str, days: int, db: AsyncSession) -> str:
    """Get the user's schedule for the next N days.

    Args:
        user_id: User's UUID as string
        days: Number of days to look ahead (default 14)
        db: Database session (injected by agent context)

    Returns:
        JSON string with upcoming schedule grouped by date
    """
    service = ScheduleService(db)
    entries = await service.get_upcoming_schedule(
        user_id=UUID(user_id),
        days=days,
    )

    # Group by date
    by_date: dict[str, list] = {}
    for entry in entries:
        date_key = entry.entry_date.isoformat()
        if date_key not in by_date:
            by_date[date_key] = []

        by_date[date_key].append({
            "id": str(entry.id),
            "type": entry.entry_type,
            "time": entry.entry_time.isoformat() if entry.entry_time else None,
            "status": entry.completion_status,
            "workout_name": entry.workout.name if entry.workout else None,
            "meal_name": entry.meal.name if entry.meal else None,
        })

    result = {
        "start_date": date.today().isoformat(),
        "days": days,
        "schedule_by_date": by_date,
    }

    return json.dumps(result, indent=2)


@function_tool
async def mark_entry_complete(entry_id: str, user_notes: str | None, db: AsyncSession) -> str:
    """Mark a schedule entry as completed.

    Args:
        entry_id: Schedule entry UUID as string
        user_notes: Optional user notes about the completion
        db: Database session (injected by agent context)

    Returns:
        JSON string with updated entry details
    """
    service = ScheduleService(db)
    entry = await service.mark_entry_complete(
        entry_id=UUID(entry_id),
        user_notes=user_notes,
    )

    result = {
        "id": str(entry.id),
        "type": entry.entry_type,
        "date": entry.entry_date.isoformat(),
        "status": entry.completion_status,
        "completed_at": entry.completed_at.isoformat() if entry.completed_at else None,
        "message": f"{entry.entry_type.capitalize()} marked as complete!",
    }

    return json.dumps(result, indent=2)


@function_tool
async def mark_entry_skipped(entry_id: str, reason: str | None, db: AsyncSession) -> str:
    """Mark a schedule entry as skipped.

    Args:
        entry_id: Schedule entry UUID as string
        reason: Optional reason for skipping
        db: Database session (injected by agent context)

    Returns:
        JSON string with updated entry details
    """
    service = ScheduleService(db)
    entry = await service.mark_entry_skipped(
        entry_id=UUID(entry_id),
        skipped_reason=reason,
    )

    result = {
        "id": str(entry.id),
        "type": entry.entry_type,
        "date": entry.entry_date.isoformat(),
        "status": entry.completion_status,
        "skipped_reason": entry.skipped_reason,
        "message": f"{entry.entry_type.capitalize()} marked as skipped.",
    }

    return json.dumps(result, indent=2)


@function_tool
async def get_next_activities(user_id: str, db: AsyncSession) -> str:
    """Get the next upcoming activities for the user.

    Useful for answering "what's next?" or "what should I do today?"

    Args:
        user_id: User's UUID as string
        db: Database session (injected by agent context)

    Returns:
        JSON string with next activities (incomplete items from today and tomorrow)
    """
    service = ScheduleService(db)
    
    # Get today's incomplete entries
    today_entries = await service.get_today_schedule(user_id=UUID(user_id))
    incomplete_today = [
        entry for entry in today_entries
        if entry.completion_status in ["scheduled", "rescheduled"]
    ]

    result = {
        "today_remaining": len(incomplete_today),
        "next_activities": [
            {
                "id": str(entry.id),
                "type": entry.entry_type,
                "time": entry.entry_time.isoformat() if entry.entry_time else None,
                "workout_name": entry.workout.name if entry.workout else None,
                "meal_name": entry.meal.name if entry.meal else None,
            }
            for entry in incomplete_today[:3]  # Show next 3
        ],
        "message": f"You have {len(incomplete_today)} activities remaining today.",
    }

    return json.dumps(result, indent=2)
