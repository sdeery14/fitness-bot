"""Structured schemas for AI agent outputs using Pydantic.

These schemas define the expected output structure from AI agents,
following OpenAI Agents SDK output types pattern.
"""
from pydantic import BaseModel, Field


class WorkoutExercise(BaseModel):
    """A single exercise in a workout."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    name: str = Field(description="Exercise name")
    sets: int = Field(description="Number of sets", ge=1, le=10)
    reps: str = Field(description="Number of reps (e.g., '8-12', '10', '30 seconds')")
    rest_seconds: int = Field(description="Rest between sets in seconds", ge=30, le=300)
    notes: str | None = Field(default=None, description="Additional instructions or form cues")


class WorkoutDay(BaseModel):
    """A single day's workout plan."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    day_name: str = Field(description="Day identifier (e.g., 'Day 1: Chest & Triceps', 'Monday')")
    focus: str = Field(description="Muscle groups or focus (e.g., 'Chest & Triceps', 'Upper Body')")
    duration_minutes: int = Field(description="Estimated workout duration in minutes", ge=20, le=120)
    warmup: str = Field(description="Warmup instructions")
    exercises: list[WorkoutExercise] = Field(description="List of exercises for this workout")
    cooldown: str = Field(description="Cooldown/stretching instructions")


class WorkoutPlan(BaseModel):
    """Complete workout plan structure."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    goal: str = Field(description="Primary fitness goal (e.g., 'Build Muscle', 'Lose Weight')")
    frequency_per_week: int = Field(description="Number of workout days per week", ge=2, le=7)
    program_type: str = Field(description="Program type (e.g., 'Push/Pull/Legs', 'Full Body', 'Upper/Lower')")
    duration_weeks: int = Field(description="Program duration in weeks", ge=4, le=16)
    workouts: list[WorkoutDay] = Field(description="List of workout days in the program")
    progression_notes: str = Field(description="How to progress the program over time")


class MealItem(BaseModel):
    """A single food item or meal component."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    name: str = Field(description="Food/meal name")
    portion: str = Field(description="Portion size (e.g., '200g', '1 cup', '2 slices')")
    calories: int = Field(description="Approximate calories", ge=0)
    protein_g: int = Field(description="Protein in grams", ge=0)
    carbs_g: int = Field(description="Carbohydrates in grams", ge=0)
    fat_g: int = Field(description="Fat in grams", ge=0)


class Meal(BaseModel):
    """A single meal in the day."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    meal_name: str = Field(description="Meal identifier (e.g., 'Breakfast', 'Post-Workout Snack')")
    time: str = Field(description="Suggested time (e.g., '7:00 AM', 'Post-workout')")
    foods: list[MealItem] = Field(description="List of foods in this meal")
    total_calories: int = Field(description="Total meal calories", ge=0)
    notes: str | None = Field(default=None, description="Preparation tips or alternatives")


class DailyMealPlan(BaseModel):
    """A single day's meal plan."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    day_name: str = Field(description="Day identifier (e.g., 'Training Day', 'Rest Day', 'Monday')")
    target_calories: int = Field(description="Target daily calories", ge=1200, le=5000)
    target_protein_g: int = Field(description="Target daily protein in grams", ge=50, le=300)
    target_carbs_g: int = Field(description="Target daily carbs in grams", ge=50, le=500)
    target_fat_g: int = Field(description="Target daily fat in grams", ge=30, le=200)
    meals: list[Meal] = Field(description="List of meals for the day")


class MealPlan(BaseModel):
    """Complete meal plan structure."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    goal: str = Field(description="Nutrition goal (e.g., 'Muscle Gain', 'Fat Loss', 'Maintenance')")
    daily_calorie_target: int = Field(description="Average daily calorie target", ge=1200, le=5000)
    macro_split: str = Field(description="Macro ratio (e.g., '40% Carbs, 30% Protein, 30% Fat')")
    meal_frequency: int = Field(description="Number of meals per day", ge=3, le=6)
    sample_days: list[DailyMealPlan] = Field(description="Sample meal plans (e.g., training day, rest day)")
    dietary_notes: str = Field(description="Dietary guidelines, restrictions, and flexibility notes")
    hydration_guidance: str = Field(description="Water intake recommendations")


class WorkoutPlanOutput(BaseModel):
    """Structured output from Workout Plan Agent."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    workout_plan: WorkoutPlan = Field(description="Complete workout program")
    key_exercises: list[str] = Field(description="Key exercises in the program")
    equipment_used: list[str] = Field(description="Equipment required for this plan")


class MealPlanOutput(BaseModel):
    """Structured output from Meal Plan Agent."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    meal_plan: MealPlan = Field(description="Complete nutrition plan")
    key_foods: list[str] = Field(description="Core foods in the meal plan")
    prep_difficulty: str = Field(description="Overall meal prep difficulty (Easy/Medium/Hard)")


class FitnessPlanOutput(BaseModel):
    """Complete fitness plan combining workout and nutrition."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    goal_summary: str = Field(description="User's primary fitness goal and context")
    duration_weeks: int = Field(description="Total program duration in weeks", ge=4, le=16)
    fitness_level: str = Field(description="User's fitness level (beginner/intermediate/advanced)")
    workout_plan_output: WorkoutPlanOutput = Field(description="Workout program from specialist agent")
    meal_plan_output: MealPlanOutput = Field(description="Nutrition plan from specialist agent")
    key_principles: list[str] = Field(description="Key principles for success (3-5 items)")
    success_metrics: list[str] = Field(description="How to measure progress (3-5 metrics)")
    important_notes: str = Field(description="Critical information about the plan")

    def validate_completeness(self) -> bool:
        """Validate that the plan is complete and well-formed.
        
        Returns:
            True if plan passes all validation checks
            
        Raises:
            ValueError: If validation fails with specific reason
        """
        # Check workout frequency matches plan duration
        workout_freq = self.workout_plan_output.workout_plan.frequency_per_week
        if not (2 <= workout_freq <= 7):
            raise ValueError(f"Invalid workout frequency: {workout_freq}. Must be 2-7 days per week.")
        
        # Check that workout duration is reasonable
        if not (4 <= self.duration_weeks <= 16):
            raise ValueError(f"Invalid duration: {self.duration_weeks}. Must be 4-16 weeks.")
        
        # Check meal plan has sample days
        if not self.meal_plan_output.meal_plan.sample_days:
            raise ValueError("Meal plan must include at least one sample day.")
        
        # Check calorie target is reasonable
        calories = self.meal_plan_output.meal_plan.daily_calorie_target
        if not (1200 <= calories <= 5000):
            raise ValueError(f"Invalid calorie target: {calories}. Must be 1200-5000.")
        
        return True


class SchedulePreferences(BaseModel):
    """User's schedule preferences for workout and meal planning."""
    
    model_config = {"extra": "allow"}  # Allow additional fields for flexibility

    split_type: str = Field(
        default="weekly_fixed",
        description="Training split type: 'weekly_fixed' (same days each week) or 'rolling' (e.g., 4-day cycle repeats regardless of calendar week)"
    )
    preferred_workout_days: list[str] | None = Field(
        default=None,
        description="Preferred days for workouts (e.g., ['Monday', 'Wednesday', 'Friday', 'Saturday']) for weekly_fixed. Leave None for rolling splits."
    )
    rest_days: list[str] | None = Field(
        default=None,
        description="Mandatory rest days (e.g., ['Sunday']) for weekly_fixed schedules"
    )
    preferred_time: str | None = Field(
        default=None,
        description="Preferred workout time: 'morning' (6-10am), 'afternoon' (12-4pm), 'evening' (5-9pm), or specific time like '6:00 AM'"
    )
    avoid_dates: list[str] | None = Field(
        default=None,
        description="Specific dates to avoid scheduling workouts (e.g., ['2025-12-25', '2026-01-01'] for holidays, travel, events). Format: YYYY-MM-DD"
    )
    notes: str | None = Field(
        default=None,
        description="Additional scheduling notes, constraints, or preferences"
    )


class ConversationRequirements(BaseModel):
    """Structured requirements extracted from conversation."""
    
    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    primary_goal: str = Field(description="Primary fitness goal")
    fitness_level: str = Field(description="Current fitness level")
    workout_frequency: int = Field(description="Days per week for working out", ge=2, le=7)
    equipment_access: str = Field(description="Equipment availability")
    time_per_session: int = Field(description="Available time per workout in minutes", ge=20, le=120)
    dietary_restrictions: list[str] = Field(default_factory=list, description="Dietary restrictions")
    injuries_or_conditions: list[str] = Field(default_factory=list, description="Injuries or health conditions")
    schedule_preferences: SchedulePreferences = Field(
        default_factory=SchedulePreferences,
        description="User's scheduling preferences and constraints"
    )
    additional_preferences: dict[str, str] = Field(default_factory=dict, description="Other preferences")

