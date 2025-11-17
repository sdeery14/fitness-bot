"""Meal plan and meal models."""

from sqlalchemy import Column, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.models import Base, TimestampMixin, UUIDMixin


class MealPlan(Base, UUIDMixin, TimestampMixin):
    """Meal plan model (FR-024, FR-025)."""

    __tablename__ = "meal_plans"

    # Plan association
    fitness_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("fitness_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Calorie and macro targets (FR-026, FR-027)
    daily_calorie_target = Column(Integer, nullable=False)
    macronutrient_distribution = Column(JSON, nullable=False)  # {"protein_percent": 30, "carbs_percent": 40, "fats_percent": 30}
    protein_grams_target = Column(Integer, nullable=False)
    carbs_grams_target = Column(Integer, nullable=False)
    fats_grams_target = Column(Integer, nullable=False)

    # Meal configuration (FR-028)
    meals_per_day = Column(Integer, nullable=False, default=3)  # 3, 4, 5, 6, etc.

    # Relationships
    fitness_plan = relationship("FitnessPlan", back_populates="meal_plans")
    meals = relationship("Meal", back_populates="meal_plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<MealPlan(id={self.id}, plan_id={self.fitness_plan_id}, calories={self.daily_calorie_target})>"


class Meal(Base, UUIDMixin, TimestampMixin):
    """Individual meal model (FR-029, FR-030, FR-044, FR-045)."""

    __tablename__ = "meals"

    # Plan association
    meal_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    phase_id = Column(PGUUID(as_uuid=True), ForeignKey("phases.id", ondelete="CASCADE"), nullable=False, index=True)

    # Meal metadata
    name = Column(String(255), nullable=False)  # "Breakfast", "Post-Workout Meal", etc.
    meal_type = Column(String(100), nullable=False)  # "breakfast", "lunch", "dinner", "snack"
    day_of_week = Column(Integer, nullable=True)  # 1-7 for scheduled meals, null for templates

    # Nutritional information (calculated from USDA data FR-044, FR-045)
    calories = Column(Integer, nullable=False)
    protein_grams = Column(Numeric(10, 2), nullable=False)
    carbs_grams = Column(Numeric(10, 2), nullable=False)
    fats_grams = Column(Numeric(10, 2), nullable=False)
    fiber_grams = Column(Numeric(10, 2), nullable=True)

    # Meal details with USDA ingredient references (FR-044, FR-045, FR-046)
    meal_details = Column(JSON, nullable=False)
    # Structure: {
    #   "ingredients": [
    #     {
    #       "usda_fdc_id": "12345",
    #       "name": "Chicken Breast",
    #       "quantity": 200,
    #       "unit": "g",
    #       "calories": 330,
    #       "protein_grams": 62,
    #       ...
    #     }
    #   ],
    #   "preparation_steps": ["Step 1", "Step 2"],
    #   "prep_time_minutes": 15,
    #   "cook_time_minutes": 20,
    #   "difficulty": "easy"
    # }

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="meals")
    phase = relationship("Phase", back_populates="meals")

    def __repr__(self) -> str:
        return f"<Meal(id={self.id}, name={self.name}, type={self.meal_type})>"
