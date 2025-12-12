"""Meal API endpoints."""
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.api.deps import CurrentUserId, DatabaseSession
from src.models.meal import Meal
from src.schemas import create_success_response

router = APIRouter()


@router.get("/{meal_id}")
async def get_meal(
    meal_id: UUID,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Get meal details.

    Args:
        meal_id: UUID of the meal
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Meal details including ingredients and nutrition

    Raises:
        HTTPException: If meal not found or user doesn't have access
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching meal {meal_id} for user {user_id}")
    
    # Query meal and verify ownership through meal_plan → fitness_plan → user
    from src.models.meal import MealPlan
    from src.models.fitness_plan import FitnessPlan
    
    stmt = (
        select(Meal)
        .join(MealPlan, Meal.meal_plan_id == MealPlan.id)
        .join(FitnessPlan, MealPlan.fitness_plan_id == FitnessPlan.id)
        .where(Meal.id == meal_id)
        .where(FitnessPlan.user_id == user_id)
    )
    logger.info(f"Executing query with JOIN")
    result = await db.execute(stmt)
    meal = result.scalar_one_or_none()
    logger.info(f"Query result: {meal}")

    if not meal:
        logger.warning(f"Meal {meal_id} not found for user {user_id}")
        raise HTTPException(status_code=404, detail="Meal not found")

    return create_success_response({
        "id": str(meal.id),
        "name": meal.name,
        "meal_type": meal.meal_type,
        "calories": meal.calories,
        "protein_grams": float(meal.protein_grams) if meal.protein_grams else 0,
        "carbs_grams": float(meal.carbs_grams) if meal.carbs_grams else 0,
        "fats_grams": float(meal.fats_grams) if meal.fats_grams else 0,
        "fiber_grams": float(meal.fiber_grams) if meal.fiber_grams else 0,
        "meal_details": meal.meal_details,
    })
