"""Meal schemas for API requests and responses."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NutritionInfo(BaseModel):
    """Nutritional information schema."""

    calories: int = Field(..., ge=0)
    protein_grams: float = Field(..., ge=0)
    carbs_grams: float = Field(..., ge=0)
    fats_grams: float = Field(..., ge=0)
    fiber_grams: Optional[float] = Field(None, ge=0)


class IngredientDetail(BaseModel):
    """Ingredient detail with USDA reference."""

    usda_fdc_id: str = Field(..., description="USDA FoodData Central ID")
    name: str
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., description="Unit: g, oz, cup, tbsp, etc.")
    calories: int
    protein_grams: float
    carbs_grams: float
    fats_grams: float
    fiber_grams: Optional[float] = None


class MealRead(BaseModel):
    """Schema for meal response."""

    id: UUID
    meal_plan_id: UUID
    phase_id: UUID
    name: str
    meal_type: str = Field(..., description="Type: breakfast, lunch, dinner, snack")
    day_of_week: Optional[int] = Field(None, ge=1, le=7, description="Day of week (1-7, null for templates)")
    calories: int
    protein_grams: float
    carbs_grams: float
    fats_grams: float
    fiber_grams: Optional[float]
    meal_details: dict = Field(..., description="Ingredients (with USDA references), preparation steps, timing")
    created_at: str

    class Config:
        from_attributes = True


class MealPlanRead(BaseModel):
    """Schema for meal plan response."""

    id: UUID
    fitness_plan_id: UUID
    daily_calorie_target: int = Field(..., ge=0)
    macronutrient_distribution: dict = Field(..., description="Macro percentages: protein, carbs, fats")
    protein_grams_target: int = Field(..., ge=0)
    carbs_grams_target: int = Field(..., ge=0)
    fats_grams_target: int = Field(..., ge=0)
    meals_per_day: int = Field(..., ge=2, le=8)
    meals: list[MealRead] = Field(default_factory=list, description="All meals in plan")

    class Config:
        from_attributes = True
