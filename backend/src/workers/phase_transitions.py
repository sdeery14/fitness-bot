"""Background tasks for phase transitions."""

import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import settings
from src.models.fitness_plan import FitnessPlan, Phase
from src.services.plan_service import PlanService
from src.workers.celery_app import celery_app


@celery_app.task(name="check_phase_transitions")
def check_phase_transitions() -> dict:
    """
    Check for users ready to transition to next phase.

    Scheduled task that runs daily to check if any users have completed
    their current phase and should transition to the next one.

    Returns:
        dict: Number of transitions processed
    """
    return asyncio.run(_check_phase_transitions_async())


async def _check_phase_transitions_async() -> dict:
    """Async implementation of phase transition checking."""
    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    transitions_triggered = 0
    errors = []

    async with async_session() as session:
        try:
            # Get all active fitness plans with phases
            stmt = (
                select(FitnessPlan)
                .where(FitnessPlan.status == "active")
                .join(Phase, Phase.fitness_plan_id == FitnessPlan.id)
                .distinct()
            )
            result = await session.execute(stmt)
            plans = list(result.scalars().all())

            # Check each plan for phase transition readiness
            plan_service = PlanService(session)

            for plan in plans:
                try:
                    # Check if this plan is ready to transition
                    phase_status = await plan_service.check_phase_completion(plan.id)

                    if phase_status.get("should_transition"):
                        # Trigger transition
                        await plan_service.transition_to_next_phase(
                            fitness_plan_id=plan.id,
                            trigger_reason="automatic_scheduled",
                        )
                        transitions_triggered += 1

                        # Queue a notification task (if notifications worker exists)
                        try:
                            from src.workers.notifications import send_phase_transition_notification

                            send_phase_transition_notification.delay(
                                user_id=str(plan.user_id),
                                fitness_plan_id=str(plan.id),
                                new_phase_name=phase_status["next_phase"]["name"],
                            )
                        except ImportError:
                            pass  # Notifications not available

                except Exception as e:
                    errors.append({
                        "plan_id": str(plan.id),
                        "error": str(e),
                    })

        finally:
            await engine.dispose()

    return {
        "status": "completed",
        "transitions_processed": transitions_triggered,
        "errors": errors,
        "error_count": len(errors),
    }


@celery_app.task(name="transition_user_phase")
def transition_user_phase(user_id: str, fitness_plan_id: str, trigger_reason: str = "manual") -> dict:
    """
    Transition user to next phase.

    Args:
        user_id: ID of the user
        fitness_plan_id: ID of the fitness plan
        trigger_reason: Reason for transition (manual, milestone, etc.)

    Returns:
        dict: Transition result
    """
    return asyncio.run(_transition_user_phase_async(user_id, fitness_plan_id, trigger_reason))


async def _transition_user_phase_async(user_id: str, fitness_plan_id: str, trigger_reason: str) -> dict:
    """Async implementation of single phase transition."""
    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            plan_service = PlanService(session)

            # Perform transition
            result = await plan_service.transition_to_next_phase(
                fitness_plan_id=UUID(fitness_plan_id),
                trigger_reason=trigger_reason,
            )

            # Queue a notification task
            try:
                from src.workers.notifications import send_phase_transition_notification

                send_phase_transition_notification.delay(
                    user_id=user_id,
                    fitness_plan_id=fitness_plan_id,
                    new_phase_name=result["transition"]["to_phase"]["name"],
                )
            except ImportError:
                pass  # Notifications not available

            return {
                "status": "success",
                "user_id": user_id,
                "fitness_plan_id": fitness_plan_id,
                "transition": result["transition"],
                "message": result["message"],
            }

        except Exception as e:
            return {
                "status": "error",
                "user_id": user_id,
                "fitness_plan_id": fitness_plan_id,
                "error": str(e),
            }
        finally:
            await engine.dispose()

