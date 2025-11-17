"""Schedule management tools for AI agents.

These tools allow AI agents to query and modify user schedules.
All tools return JSON strings as required by OpenAI Agents SDK.
"""
import json
from datetime import date, datetime
from uuid import UUID

from agents import function_tool
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import DisruptionEvent
from src.models.schedule import ScheduleEntry
from src.services.schedule_service import ScheduleService
from src.services.user_service import UserService


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


@function_tool
async def reschedule_after_disruption(
    user_id: str,
    fitness_plan_id: str,
    disruption_type: str,
    start_date: str,
    end_date: str | None,
    description: str,
    severity: str,
    db: AsyncSession,
) -> str:
    """Reschedule user's plan after a disruption (illness, injury, travel, etc.).

    Intelligently rearranges workouts and meals, potentially extending the
    plan timeline to accommodate the disruption.

    Args:
        user_id: User's UUID as string
        fitness_plan_id: FitnessPlan UUID as string
        disruption_type: Type - 'illness', 'injury', 'travel', 'schedule_conflict', 'other'
        start_date: Disruption start date (ISO format YYYY-MM-DD)
        end_date: Disruption end date (ISO format, null if ongoing)
        description: Detailed description of the disruption
        severity: Severity level - 'minor', 'moderate', 'severe'
        db: Database session (injected by agent context)

    Returns:
        JSON string with rescheduling details and new plan timeline
    """
    # Create DisruptionEvent
    disruption = DisruptionEvent(
        user_id=UUID(user_id),
        fitness_plan_id=UUID(fitness_plan_id),
        disruption_type=disruption_type,
        start_date=datetime.fromisoformat(start_date).date(),
        end_date=datetime.fromisoformat(end_date).date() if end_date else None,
        description=description,
        severity=severity,
        resolution_strategy="reschedule",  # Will be updated by service
        status="processing",
    )
    db.add(disruption)
    await db.flush()  # Get disruption ID

    # Execute rescheduling logic
    service = ScheduleService(db)
    result = await service.reschedule_for_disruption(disruption)

    # Update disruption record with results
    disruption.workouts_affected = result["workouts_affected"]
    disruption.meals_affected = result["meals_affected"]
    disruption.timeline_extension_days = result["timeline_extension_days"]
    disruption.resolution_strategy = result["strategy_applied"]
    disruption.resolution_details = {
        "rescheduled_workouts": result["rescheduled_workouts"],
        "rescheduled_meals": result["rescheduled_meals"],
        "new_end_date": result["new_end_date"].isoformat() if result["new_end_date"] else None,
    }
    disruption.status = "resolved"

    await db.commit()

    # Build AI-friendly response
    ai_response = {
        "disruption_id": str(disruption.id),
        "resolution_strategy": result["strategy_applied"],
        "workouts_affected": result["workouts_affected"],
        "meals_affected": result["meals_affected"],
        "timeline_extension_days": result["timeline_extension_days"],
        "new_end_date": result["new_end_date"].isoformat() if result["new_end_date"] else None,
        "message": f"I've rescheduled your plan to accommodate your {disruption_type}. "
                   f"Affected: {result['workouts_affected']} workouts, {result['meals_affected']} meals. "
                   + (f"Extended timeline by {result['timeline_extension_days']} days." if result['timeline_extension_days'] > 0 else "No timeline extension needed."),
    }

    return json.dumps(ai_response, indent=2)


@function_tool
async def suggest_rest_days(
    user_id: str,
    fitness_plan_id: str,
    db: AsyncSession,
) -> str:
    """Suggest rest days to prevent overtraining based on activity patterns.

    Analyzes recent workout frequency and completion rates to recommend
    when the user should take rest days.

    Args:
        user_id: User's UUID as string
        fitness_plan_id: FitnessPlan UUID as string
        db: Database session (injected by agent context)

    Returns:
        JSON string with rest day recommendations
    """
    # Check for inactivity/overtraining patterns
    user_service = UserService(db)
    inactivity_check = await user_service.check_inactivity(
        user_id=UUID(user_id),
        fitness_plan_id=UUID(fitness_plan_id),
        inactivity_threshold_days=14,
    )

    # Get upcoming schedule to analyze workout density
    schedule_service = ScheduleService(db)
    upcoming = await schedule_service.get_upcoming_schedule(
        user_id=UUID(user_id),
        days=7,
    )

    # Count workouts in next 7 days
    workout_count = sum(1 for entry in upcoming if entry.entry_type == "workout" and entry.completion_status in ["scheduled", "rescheduled"])

    # Determine recommendation
    if inactivity_check["is_inactive"]:
        recommendation = {
            "needs_rest": False,
            "reason": "inactive",
            "message": f"You've been inactive for {inactivity_check['days_since_last_activity']} days. "
                       "Focus on gradually resuming activity rather than rest.",
        }
    elif workout_count >= 6:
        recommendation = {
            "needs_rest": True,
            "reason": "overtraining_risk",
            "suggested_rest_days": 2,
            "message": f"You have {workout_count} workouts scheduled in the next 7 days. "
                       "Consider taking 1-2 rest days to prevent overtraining and allow recovery.",
        }
    elif workout_count >= 4:
        recommendation = {
            "needs_rest": False,
            "reason": "balanced",
            "message": f"Your schedule looks balanced with {workout_count} workouts in the next 7 days. "
                       "Continue as planned, but listen to your body.",
        }
    else:
        recommendation = {
            "needs_rest": False,
            "reason": "light_schedule",
            "message": f"You have {workout_count} workouts scheduled. This is a lighter week - "
                       "you're getting adequate rest.",
        }

    return json.dumps(recommendation, indent=2)
