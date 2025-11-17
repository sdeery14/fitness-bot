"""Background tasks for schedule recalculation."""

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import AsyncSessionLocal
from src.models.conversation import DisruptionEvent
from src.services.schedule_service import ScheduleService
from src.services.user_service import UserService
from src.workers.celery_app import celery_app


@celery_app.task(name="recalculate_schedule_for_disruption")
def recalculate_schedule_for_disruption(disruption_id: str) -> dict:
    """
    Recalculate schedule after a disruption event (FR-016, FR-017, FR-018).

    This is a background task for complex rescheduling operations that may
    take time. The AI agent creates a DisruptionEvent and queues this task
    to handle the actual rescheduling asynchronously.

    Args:
        disruption_id: UUID of the DisruptionEvent to process

    Returns:
        dict: Recalculation result with status and details
    """
    async def _process_disruption():
        async with AsyncSessionLocal() as db:
            # Load the disruption event
            from sqlalchemy import select
            stmt = select(DisruptionEvent).where(DisruptionEvent.id == UUID(disruption_id))
            result = await db.execute(stmt)
            disruption = result.scalar_one_or_none()

            if not disruption:
                return {
                    "status": "error",
                    "message": f"Disruption {disruption_id} not found",
                }

            # Mark as processing
            disruption.status = "processing"
            await db.commit()

            try:
                # Execute rescheduling logic
                service = ScheduleService(db)
                result = await service.reschedule_for_disruption(disruption)

                # Update disruption with results
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

                return {
                    "status": "success",
                    "disruption_id": disruption_id,
                    "workouts_affected": result["workouts_affected"],
                    "meals_affected": result["meals_affected"],
                    "timeline_extension_days": result["timeline_extension_days"],
                    "strategy": result["strategy_applied"],
                }

            except Exception as e:
                # Mark as failed
                disruption.status = "reported"  # Reset to allow retry
                await db.commit()
                return {
                    "status": "error",
                    "message": f"Rescheduling failed: {str(e)}",
                    "disruption_id": disruption_id,
                }

    # Run the async function
    return asyncio.run(_process_disruption())


@celery_app.task(name="check_user_inactivity")
def check_user_inactivity(user_id: str, fitness_plan_id: str) -> dict:
    """
    Check for user inactivity and trigger notifications or reassessment (FR-059, FR-060).

    Scheduled task that runs periodically to detect users who haven't
    logged progress in 14+ days.

    Args:
        user_id: UUID of the user to check
        fitness_plan_id: UUID of the fitness plan to check

    Returns:
        dict: Inactivity check result with recommendation
    """
    async def _check_inactivity():
        async with AsyncSessionLocal() as db:
            service = UserService(db)
            result = await service.check_inactivity(
                user_id=UUID(user_id),
                fitness_plan_id=UUID(fitness_plan_id),
                inactivity_threshold_days=14,
            )

            # If user is inactive, could trigger notification here
            if result["is_inactive"]:
                # TODO: Integrate with notification system
                result["notification_sent"] = False
                result["action_needed"] = "Send re-engagement email or push notification"

            return result

    return asyncio.run(_check_inactivity())


@celery_app.task(name="process_missed_workouts")
def process_missed_workouts(user_id: str, fitness_plan_id: str, days_to_check: int = 7) -> dict:
    """
    Process missed workouts and suggest rescheduling if needed.

    Analyzes recent schedule adherence and identifies patterns of missed
    workouts that may require schedule adjustment.

    Args:
        user_id: UUID of the user
        fitness_plan_id: UUID of the fitness plan
        days_to_check: Number of days to look back (default 7)

    Returns:
        dict: Analysis of missed workouts with recommendations
    """
    async def _process_missed():
        async with AsyncSessionLocal() as db:
            from datetime import date, timedelta
            from sqlalchemy import and_, select

            # Get schedule entries from past N days
            from src.models.schedule import Schedule, ScheduleEntry
            start_date = date.today() - timedelta(days=days_to_check)

            stmt = (
                select(ScheduleEntry)
                .join(Schedule)
                .where(
                    and_(
                        Schedule.user_id == UUID(user_id),
                        Schedule.fitness_plan_id == UUID(fitness_plan_id),
                        ScheduleEntry.entry_date >= start_date,
                        ScheduleEntry.entry_date <= date.today(),
                        ScheduleEntry.entry_type == "workout",
                    )
                )
            )
            result = await db.execute(stmt)
            entries = list(result.scalars().all())

            # Analyze completion status
            total_workouts = len(entries)
            completed = sum(1 for e in entries if e.completion_status == "completed")
            skipped = sum(1 for e in entries if e.completion_status == "skipped")
            missed = sum(1 for e in entries if e.completion_status in ["scheduled", "rescheduled"] and e.entry_date < date.today())

            adherence_rate = (completed / total_workouts * 100) if total_workouts > 0 else 0

            # Determine recommendation
            if adherence_rate < 50 and missed > 3:
                recommendation = "reschedule"
                message = f"Low adherence ({adherence_rate:.0f}%) with {missed} missed workouts. Consider rescheduling."
            elif adherence_rate < 70 and missed > 2:
                recommendation = "check_in"
                message = f"Moderate adherence ({adherence_rate:.0f}%). Check if user needs support."
            else:
                recommendation = "continue"
                message = f"Good adherence ({adherence_rate:.0f}%). Keep going!"

            return {
                "user_id": user_id,
                "fitness_plan_id": fitness_plan_id,
                "days_checked": days_to_check,
                "total_workouts": total_workouts,
                "completed": completed,
                "skipped": skipped,
                "missed": missed,
                "adherence_rate": round(adherence_rate, 1),
                "recommendation": recommendation,
                "message": message,
            }

    return asyncio.run(_process_missed())
