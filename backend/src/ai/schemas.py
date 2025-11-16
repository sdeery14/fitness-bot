"""Structured schemas for AI agent outputs using Pydantic.

These schemas define the expected output structure from AI agents,
following OpenAI Agents SDK output types pattern.
"""
from pydantic import BaseModel, Field


class WorkoutExercise(BaseModel):
    """A single exercise in a workout."""

    name: str = Field(description="Exercise name")
    sets: int = Field(description="Number of sets", ge=1, le=10)
    reps: str = Field(description="Number of reps (e.g., '8-12', '10', '30 seconds')")
    rest_seconds: int = Field(description="Rest between sets in seconds", ge=30, le=300)
    notes: str | None = Field(default=None, description="Additional instructions or form cues")


class WorkoutDay(BaseModel):
    """A single day's workout plan."""

    day_name: str = Field(description="Day identifier (e.g., 'Day 1: Chest & Triceps', 'Monday')")
    focus: str = Field(description="Muscle groups or focus (e.g., 'Chest & Triceps', 'Upper Body')")
    duration_minutes: int = Field(description="Estimated workout duration in minutes", ge=20, le=120)
    warmup: str = Field(description="Warmup instructions")
    exercises: list[WorkoutExercise] = Field(description="List of exercises for this workout")
    cooldown: str = Field(description="Cooldown/stretching instructions")


class WorkoutPlan(BaseModel):
    """Complete workout plan structure."""

    goal: str = Field(description="Primary fitness goal (e.g., 'Build Muscle', 'Lose Weight')")
    frequency_per_week: int = Field(description="Number of workout days per week", ge=2, le=7)
    program_type: str = Field(description="Program type (e.g., 'Push/Pull/Legs', 'Full Body', 'Upper/Lower')")
    duration_weeks: int = Field(description="Program duration in weeks", ge=4, le=16)
    workouts: list[WorkoutDay] = Field(description="List of workout days in the program")
    progression_notes: str = Field(description="How to progress the program over time")


class MealItem(BaseModel):
    """A single food item or meal component."""

    name: str = Field(description="Food/meal name")
    portion: str = Field(description="Portion size (e.g., '200g', '1 cup', '2 slices')")
    calories: int = Field(description="Approximate calories", ge=0)
    protein_g: int = Field(description="Protein in grams", ge=0)
    carbs_g: int = Field(description="Carbohydrates in grams", ge=0)
    fat_g: int = Field(description="Fat in grams", ge=0)


class Meal(BaseModel):
    """A single meal in the day."""

    meal_name: str = Field(description="Meal identifier (e.g., 'Breakfast', 'Post-Workout Snack')")
    time: str = Field(description="Suggested time (e.g., '7:00 AM', 'Post-workout')")
    foods: list[MealItem] = Field(description="List of foods in this meal")
    total_calories: int = Field(description="Total meal calories", ge=0)
    notes: str | None = Field(default=None, description="Preparation tips or alternatives")


class DailyMealPlan(BaseModel):
    """A single day's meal plan."""

    day_name: str = Field(description="Day identifier (e.g., 'Training Day', 'Rest Day', 'Monday')")
    target_calories: int = Field(description="Target daily calories", ge=1200, le=5000)
    target_protein_g: int = Field(description="Target daily protein in grams", ge=50, le=300)
    target_carbs_g: int = Field(description="Target daily carbs in grams", ge=50, le=500)
    target_fat_g: int = Field(description="Target daily fat in grams", ge=30, le=200)
    meals: list[Meal] = Field(description="List of meals for the day")


class MealPlan(BaseModel):
    """Complete meal plan structure."""

    goal: str = Field(description="Nutrition goal (e.g., 'Muscle Gain', 'Fat Loss', 'Maintenance')")
    daily_calorie_target: int = Field(description="Average daily calorie target", ge=1200, le=5000)
    macro_split: str = Field(description="Macro ratio (e.g., '40% Carbs, 30% Protein, 30% Fat')")
    meal_frequency: int = Field(description="Number of meals per day", ge=3, le=6)
    sample_days: list[DailyMealPlan] = Field(description="Sample meal plans (e.g., training day, rest day)")
    dietary_notes: str = Field(description="Dietary guidelines, restrictions, and flexibility notes")
    hydration_guidance: str = Field(description="Water intake recommendations")


class FitnessPlanOutput(BaseModel):
    """Complete fitness plan combining workout and nutrition."""

    goal_summary: str = Field(description="User's primary fitness goal and context")
    duration_weeks: int = Field(description="Total program duration in weeks", ge=4, le=16)
    fitness_level: str = Field(description="User's fitness level (beginner/intermediate/advanced)")
    workout_plan: WorkoutPlan = Field(description="Complete workout program")
    meal_plan: MealPlan = Field(description="Complete nutrition plan")
    key_principles: list[str] = Field(description="Key principles for success (3-5 items)")
    success_metrics: list[str] = Field(description="How to measure progress (3-5 metrics)")
    important_notes: str = Field(description="Critical information about the plan")


class ConversationRequirements(BaseModel):
    """Structured requirements extracted from conversation."""

    primary_goal: str = Field(description="Primary fitness goal")
    fitness_level: str = Field(description="Current fitness level")
    workout_frequency: int = Field(description="Days per week for working out", ge=2, le=7)
    equipment_access: str = Field(description="Equipment availability")
    time_per_session: int = Field(description="Available time per workout in minutes", ge=20, le=120)
    dietary_restrictions: list[str] = Field(default_factory=list, description="Dietary restrictions")
    injuries_or_conditions: list[str] = Field(default_factory=list, description="Injuries or health conditions")
    additional_preferences: dict = Field(default_factory=dict, description="Other preferences")

