"""Meal API endpoints."""
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.api.deps import CurrentUserId, DatabaseSession
from src.models.meal import Meal
from src.schemas import create_success_response

router = APIRouter(prefix="/meals", tags=["meals"])


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
        HTTPException: If meal not found
    """
    stmt = select(Meal).where(Meal.id == meal_id)
    result = await db.execute(stmt)
    meal = result.scalar_one_or_none()

    if not meal:
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
