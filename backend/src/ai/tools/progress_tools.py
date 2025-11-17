"""Progress tracking tools for AI agents.

These tools allow AI agents to query user progress and adherence metrics.
All tools return JSON strings as required by OpenAI Agents SDK.
"""
import json
from datetime import date, timedelta
from uuid import UUID

from agents import function_tool
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.progress_service import ProgressService


@function_tool
async def get_adherence_stats(user_id: str, days: int, db: AsyncSession) -> str:
    """Get adherence statistics for a user over the last N days.

    Args:
        user_id: User's UUID as string
        days: Number of days to analyze (default 7 for weekly)
        db: Database session (injected by agent context)

    Returns:
        JSON string with adherence percentages and completion counts
    """
    service = ProgressService(db)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    stats = await service.calculate_adherence(
        user_id=UUID(user_id),
        start_date=start_date,
        end_date=end_date,
    )

    # Convert Decimal to float for JSON serialization
    result = {
        "period": f"Last {days} days",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "overall_adherence": float(stats["overall_adherence"]),
        "workout_adherence": float(stats["workout_adherence"]),
        "meal_adherence": float(stats["meal_adherence"]),
        "total_scheduled": stats["total_scheduled"],
        "total_completed": stats["total_completed"],
        "workouts_completed": stats["workouts_completed"],
        "meals_completed": stats["meals_completed"],
    }

    return json.dumps(result, indent=2)



@function_tool
async def get_progress_summary(user_id: str, db: AsyncSession) -> str:
    """Get comprehensive progress summary for a user.

    Args:
        user_id: User's UUID as string
        db: Database session (injected by agent context)

    Returns:
        JSON string with streak, adherence, milestones, and measurements
    """
    service = ProgressService(db)
    summary = await service.get_progress_summary(user_id=UUID(user_id))

    # Convert nested Decimals to floats
    weekly = summary["weekly_adherence"]
    monthly = summary["monthly_adherence"]

    result = {
        "current_streak_days": summary["current_streak_days"],
        "weekly_adherence": {
            "overall": float(weekly["overall_adherence"]),
            "workouts": float(weekly["workout_adherence"]),
            "meals": float(weekly["meal_adherence"]),
        },
        "monthly_adherence": {
            "overall": float(monthly["overall_adherence"]),
            "workouts": float(monthly["workout_adherence"]),
            "meals": float(monthly["meal_adherence"]),
        },
        "total_workouts_completed": summary["total_workouts_completed"],
        "recent_milestones": summary["recent_milestones"],
        "latest_measurements": summary["latest_measurements"],
    }

    return json.dumps(result, indent=2)


@function_tool
async def get_current_streak(user_id: str, db: AsyncSession) -> str:
    """Get the user's current streak of consecutive active days.

    Args:
        user_id: User's UUID as string
        db: Database session (injected by agent context)

    Returns:
        JSON string with streak count and encouraging message
    """
    service = ProgressService(db)
    streak = await service.get_streak(user_id=UUID(user_id))

    messages = {
        0: "No current streak. Let's start one today!",
        1: "You're on a 1-day streak! Keep it going!",
        range(2, 7): f"Great! You're on a {streak}-day streak!",
        range(7, 14): f"Impressive {streak}-day streak! You're building consistency!",
        range(14, 30): f"Outstanding {streak}-day streak! You're on fire!",
    }

    message = "Amazing dedication!"
    for days, msg in messages.items():
        if isinstance(days, range) and streak in days:
            message = msg
            break
        elif isinstance(days, int) and streak == days:
            message = msg
            break

    result = {
        "current_streak_days": streak,
        "message": message,
    }

    return json.dumps(result, indent=2)


@function_tool
async def calculate_progress_percentage(user_id: str, fitness_plan_id: str, db: AsyncSession) -> str:
    """Calculate how far through the plan the user is based on completion.

    Args:
        user_id: User's UUID as string
        fitness_plan_id: Fitness plan UUID as string
        db: Database session (injected by agent context)

    Returns:
        JSON string with completion percentage and remaining activities
    """
    from sqlalchemy import and_, func, select
    from src.models.schedule import Schedule, ScheduleEntry

    # Count total and completed entries for this plan
    stmt = (
        select(
            func.count(ScheduleEntry.id).label("total"),
            func.sum(
                func.case((ScheduleEntry.completion_status == "completed", 1), else_=0)
            ).label("completed"),
        )
        .join(Schedule)
        .where(
            and_(
                Schedule.user_id == UUID(user_id),
                Schedule.fitness_plan_id == UUID(fitness_plan_id),
            )
        )
    )

    result_db = await db.execute(stmt)
    row = result_db.first()

    total = row.total if row else 0
    completed = row.completed if row else 0

    percentage = (completed / total * 100) if total > 0 else 0

    result = {
        "total_activities": total,
        "completed_activities": completed,
        "completion_percentage": round(percentage, 1),
        "remaining_activities": total - completed,
        "message": f"You've completed {completed} out of {total} activities ({percentage:.1f}%)!",
    }

    return json.dumps(result, indent=2)
