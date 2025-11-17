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


@function_tool
def analyze_adherence_patterns(user_id: str, days: int = 30) -> str:
    """Analyze user's adherence patterns to identify trends and issues.

    Args:
        user_id: User's UUID as string
        days: Number of days to analyze (default 30)

    Returns:
        JSON string with adherence patterns, trends, and recommendations
    """
    import asyncio

    from sqlalchemy import and_, select

    from src.database import AsyncSessionLocal
    from src.models.schedule import Schedule, ScheduleEntry

    async def _analyze():
        async with AsyncSessionLocal() as db:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Get schedule entries for period
            stmt = (
                select(ScheduleEntry)
                .join(Schedule)
                .where(
                    and_(
                        Schedule.user_id == UUID(user_id),
                        ScheduleEntry.schedule_date >= start_date,
                        ScheduleEntry.schedule_date <= end_date,
                    )
                )
                .order_by(ScheduleEntry.schedule_date)
            )

            result = await db.execute(stmt)
            entries = result.scalars().all()

            if not entries:
                return {
                    "error": "No activity data found for analysis period",
                    "recommendation": "Start tracking your activities to see patterns",
                }

            # Analyze patterns
            total_entries = len(entries)
            completed_entries = sum(1 for e in entries if e.completion_status == "completed")
            workout_entries = sum(1 for e in entries if e.workout_id)
            meal_entries = sum(1 for e in entries if e.meal_id)
            completed_workouts = sum(
                1 for e in entries if e.workout_id and e.completion_status == "completed"
            )
            completed_meals = sum(
                1 for e in entries if e.meal_id and e.completion_status == "completed"
            )

            # Calculate adherence rates
            overall_adherence = (completed_entries / total_entries * 100) if total_entries > 0 else 0
            workout_adherence = (
                (completed_workouts / workout_entries * 100) if workout_entries > 0 else 0
            )
            meal_adherence = (completed_meals / meal_entries * 100) if meal_entries > 0 else 0

            # Identify weak days (days of week with lower adherence)
            from collections import defaultdict

            day_adherence = defaultdict(lambda: {"total": 0, "completed": 0})
            for entry in entries:
                day_name = entry.schedule_date.strftime("%A")
                day_adherence[day_name]["total"] += 1
                if entry.completion_status == "completed":
                    day_adherence[day_name]["completed"] += 1

            weak_days = []
            for day, stats in day_adherence.items():
                day_rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
                if day_rate < 70:  # Less than 70% adherence
                    weak_days.append({"day": day, "adherence_rate": round(day_rate, 1)})

            # Generate recommendations
            recommendations = []
            if overall_adherence < 70:
                recommendations.append(
                    "Overall adherence is below target. Consider adjusting your schedule to be more realistic."
                )
            if workout_adherence < meal_adherence - 20:
                recommendations.append(
                    "Workout adherence is significantly lower than meal adherence. "
                    "Consider shorter or more flexible workout options."
                )
            if meal_adherence < workout_adherence - 20:
                recommendations.append(
                    "Meal adherence is significantly lower than workout adherence. "
                    "Consider meal prep or simpler meal plans."
                )
            if weak_days:
                weak_day_names = ", ".join([d["day"] for d in weak_days])
                recommendations.append(
                    f"Adherence is lower on: {weak_day_names}. "
                    "Consider adjusting activities on these days or identifying barriers."
                )
            if overall_adherence >= 80:
                recommendations.append(
                    "Excellent adherence! You might be ready to increase intensity or add new goals."
                )

            return {
                "analysis_period": f"{start_date.isoformat()} to {end_date.isoformat()}",
                "overall_adherence": round(overall_adherence, 1),
                "workout_adherence": round(workout_adherence, 1),
                "meal_adherence": round(meal_adherence, 1),
                "total_activities": total_entries,
                "completed_activities": completed_entries,
                "weak_days": weak_days,
                "trends": {
                    "workouts": f"{completed_workouts}/{workout_entries} completed",
                    "meals": f"{completed_meals}/{meal_entries} completed",
                },
                "recommendations": recommendations,
            }

    result = asyncio.run(_analyze())
    return json.dumps(result, indent=2)


@function_tool
def suggest_improvements(user_id: str, fitness_plan_id: str) -> str:
    """Suggest plan improvements based on adherence and progress analysis.

    Args:
        user_id: User's UUID as string
        fitness_plan_id: Fitness plan UUID as string

    Returns:
        JSON string with improvement suggestions
    """
    import asyncio

    from sqlalchemy import and_, select

    from src.database import AsyncSessionLocal
    from src.models.fitness_plan import FitnessPlan
    from src.models.schedule import Schedule, ScheduleEntry

    async def _suggest():
        async with AsyncSessionLocal() as db:
            # Get recent adherence (last 14 days)
            end_date = date.today()
            start_date = end_date - timedelta(days=14)

            stmt = (
                select(ScheduleEntry)
                .join(Schedule)
                .where(
                    and_(
                        Schedule.user_id == UUID(user_id),
                        Schedule.fitness_plan_id == UUID(fitness_plan_id),
                        ScheduleEntry.schedule_date >= start_date,
                        ScheduleEntry.schedule_date <= end_date,
                    )
                )
            )

            result = await db.execute(stmt)
            entries = result.scalars().all()

            # Get plan details
            plan_stmt = select(FitnessPlan).where(FitnessPlan.id == UUID(fitness_plan_id))
            plan_result = await db.execute(plan_stmt)
            plan = plan_result.scalar_one_or_none()

            if not plan:
                return {"error": "Fitness plan not found"}

            if not entries:
                return {
                    "message": "Not enough recent data for improvement suggestions",
                    "recommendation": "Complete activities for at least 2 weeks to get personalized suggestions",
                }

            total = len(entries)
            completed = sum(1 for e in entries if e.completion_status == "completed")
            adherence = (completed / total * 100) if total > 0 else 0

            suggestions = []

            # Low adherence suggestions
            if adherence < 50:
                suggestions.append({
                    "category": "Schedule Adjustment",
                    "priority": "high",
                    "suggestion": "Reduce workout frequency to build consistency",
                    "rationale": f"Current adherence is {adherence:.0f}%. Starting with fewer sessions can help establish a habit.",
                    "action": "Decrease weekly workouts by 1-2 sessions",
                })

            elif adherence < 70:
                suggestions.append({
                    "category": "Flexibility",
                    "priority": "medium",
                    "suggestion": "Add flexible workout options",
                    "rationale": f"Adherence at {adherence:.0f}% suggests some barriers exist.",
                    "action": "Consider adding home workout alternatives or shorter sessions",
                })

            # Good adherence - progression suggestions
            elif adherence >= 80:
                suggestions.append({
                    "category": "Progression",
                    "priority": "medium",
                    "suggestion": "Consider progressive overload",
                    "rationale": f"Strong {adherence:.0f}% adherence indicates readiness for progression.",
                    "action": "Gradually increase workout intensity by 10-15%",
                })

            # Check for missed workout patterns
            missed_workouts = sum(
                1
                for e in entries
                if e.workout_id
                and e.completion_status in ["missed", "rescheduled", "skipped"]
            )
            if missed_workouts > total * 0.3:
                suggestions.append({
                    "category": "Workout Modifications",
                    "priority": "high",
                    "suggestion": "Simplify workout requirements",
                    "rationale": "High rate of missed workouts suggests workouts may be too demanding",
                    "action": "Consider shorter sessions or bodyweight alternatives",
                })

            # Time-based suggestions
            plan_start = plan.start_date
            days_active = (date.today() - plan_start).days if plan_start else 0

            if days_active >= 30 and adherence >= 75:
                suggestions.append({
                    "category": "New Goals",
                    "priority": "low",
                    "suggestion": "Consider adding complementary goals",
                    "rationale": f"You've maintained {adherence:.0f}% adherence for {days_active} days",
                    "action": "Add flexibility work, cardio, or skill-based training",
                })

            return {
                "user_id": user_id,
                "fitness_plan_id": fitness_plan_id,
                "analysis_period": f"Last 14 days ({start_date} to {end_date})",
                "current_adherence": round(adherence, 1),
                "total_activities": total,
                "completed_activities": completed,
                "suggestions": suggestions,
                "overall_assessment": (
                    "Excellent progress!" if adherence >= 80
                    else "Good progress, minor adjustments recommended" if adherence >= 70
                    else "Consider plan adjustments to improve adherence"
                ),
            }

    result = asyncio.run(_suggest())
    return json.dumps(result, indent=2)

