"""Background tasks for sending notifications."""

from src.workers.celery_app import celery_app


@celery_app.task(name="send_workout_reminder")
def send_workout_reminder(user_id: str, workout_id: str) -> dict:
    """
    Send workout reminder notification to user.

    Args:
        user_id: ID of the user
        workout_id: ID of the scheduled workout

    Returns:
        dict: Notification status
    """
    # TODO: Implement notification sending
    return {
        "status": "pending",
        "message": "Notification system not yet implemented",
        "user_id": user_id,
        "workout_id": workout_id,
    }


@celery_app.task(name="send_phase_completion_notification")
def send_phase_completion_notification(user_id: str, phase_id: str) -> dict:
    """
    Send phase completion notification to user.
    
    Args:
        user_id: ID of the user
        phase_id: ID of the completed phase
        
    Returns:
        dict: Notification status
    """
    # TODO: Implement phase completion notification
    return {
        "status": "pending",
        "message": "Notification system not yet implemented",
        "user_id": user_id,
        "phase_id": phase_id,
    }
