"""Structured schemas for AI agent outputs using Pydantic.

These schemas define the expected output structure from AI agents,
following OpenAI Agents SDK output types pattern.
"""

from pydantic import BaseModel, Field


class WorkoutExercise(BaseModel):
    """A single exercise in a workout with complete prescription details."""

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    name: str = Field(description="Exercise name (e.g., 'Barbell Bench Press', 'Dumbbell Romanian Deadlift')")
    exercise_type: str = Field(
        description="Exercise type: 'compound', 'isolation', 'cardio', 'plyometric', 'stretch', or 'core'"
    )
    target_muscle_groups: list[str] = Field(
        description="Primary muscle groups targeted (e.g., ['chest', 'triceps', 'shoulders']). Use lowercase.",
        min_length=1
    )
    equipment_required: list[str] = Field(
        description="Equipment needed (e.g., ['barbell', 'bench'], or ['bodyweight'] for no equipment). Use lowercase.",
        min_length=1
    )
    sets: int | None = Field(
        default=None,
        description="Number of sets (null for time-based cardio exercises)", 
        ge=1, 
        le=10
    )
    reps: str | None = Field(
        default=None,
        description="Number of reps (e.g., '8-12', '10', 'AMRAP', or null for time-based exercises)"
    )
    duration_seconds: int | None = Field(
        default=None,
        description="Duration for timed exercises like planks or cardio (null for rep-based exercises)",
        ge=10,
        le=3600
    )
    rest_seconds: int = Field(
        description="Rest period between sets in seconds", 
        ge=30, 
        le=300
    )
    tempo: str | None = Field(
        default=None,
        description="Tempo prescription in format 'eccentric-pause-concentric-pause' (e.g., '3-1-1-0' for 3s down, 1s pause, 1s up, no pause at top)"
    )
    rpe_target: int | None = Field(
        default=None,
        description="Target Rate of Perceived Exertion on 1-10 scale (e.g., 8 = 2 reps in reserve)",
        ge=1,
        le=10
    )
    instructions: str = Field(
        description="Detailed step-by-step execution instructions (2-4 sentences covering setup, movement, and key points)"
    )
    form_cues: list[str] = Field(
        default_factory=list,
        description="2-4 specific form cues to focus on (e.g., 'Keep core tight', 'Full range of motion', 'Control the eccentric')"
    )


class WorkoutDay(BaseModel):
    """A single day's workout plan with complete exercise details."""

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    day_name: str = Field(description="Day identifier (e.g., 'Day 1: Chest & Triceps', 'Monday', 'Upper Body Push')")
    focus: str = Field(description="Muscle groups or focus (e.g., 'Chest & Triceps', 'Upper Body', 'Full Body')")
    workout_type: str = Field(
        description="Primary workout type: 'strength', 'hypertrophy', 'cardio', 'flexibility', 'hybrid', or 'power'"
    )
    intensity_level: str = Field(
        description="Intensity level for this workout: 'low', 'moderate', or 'high'"
    )
    duration_minutes: int = Field(
        description="Estimated workout duration in minutes", ge=20, le=120
    )
    warmup: str = Field(description="Warmup instructions (2-3 sentences)")
    exercises: list[WorkoutExercise] = Field(
        description="List of exercises for this workout with complete prescription details",
        min_length=1
    )
    cooldown: str = Field(description="Cooldown/stretching instructions (2-3 sentences)")
    notes: str | None = Field(
        default=None,
        description="Additional workout notes or coaching cues"
    )


class RestDay(BaseModel):
    """Represents a rest day in the training cycle."""

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    day_name: str = Field(default="Rest Day", description="Rest day identifier")
    notes: str | None = Field(
        default=None,
        description="Optional rest day guidance (e.g., 'Light stretching', 'Active recovery walk')",
    )


class WorkoutCycleItem(BaseModel):
    """A single item in the training cycle (workout or rest).

    This defines the order and structure of the training cycle, allowing for:
    - Rolling splits (e.g., Upper/Lower/Rest repeating regardless of calendar week)
    - Weekly fixed schedules (specific days mapped to specific workouts)
    - Mixed schedules (workouts with built-in rest days)
    """

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    type: str = Field(description="Item type: 'workout' or 'rest'")
    workout_index: int | None = Field(
        default=None,
        description="Index into workouts list (for type='workout'). 0-based index.",
    )
    rest_day: RestDay | None = Field(
        default=None, description="Rest day information (for type='rest')"
    )


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
    prep_type: str | None = Field(
        default="quick_assembly", 
        description="Meal preparation type: 'batch_prepped' (cooked in advance), 'fresh_cook' (cook day-of), or 'quick_assembly' (no cooking needed)"
    )
    prep_instructions: str | None = Field(
        default=None,
        description="Day-of cooking or assembly instructions if needed (for fresh_cook or quick_assembly meals)"
    )
    storage_notes: str | None = Field(
        default=None,
        description="How to store if batch-prepped (e.g., 'Store in airtight containers, refrigerate up to 4 days, reheat at 350°F for 10 min')"
    )


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
    sample_days: list[DailyMealPlan] = Field(
        description="Sample meal plans (e.g., training day, rest day)"
    )
    dietary_notes: str = Field(
        description="Dietary guidelines, restrictions, and flexibility notes"
    )
    hydration_guidance: str = Field(description="Water intake recommendations")


class WorkoutPlanMetadata(BaseModel):
    """Plan-level workout metadata that applies across all phases."""

    model_config = {"extra": "forbid"}

    program_type: str = Field(
        description="Training split type (e.g., 'Push/Pull/Legs', 'Upper/Lower', 'Full Body', 'Bro Split')"
    )
    progression_strategy: str = Field(
        description="How to progress over time (e.g., 'Linear progression', 'Double progression', 'DUP', 'Wave loading')"
    )
    training_principles: list[str] = Field(
        description="Key training principles for the program (e.g., 'Progressive overload', 'Mind-muscle connection', 'Controlled tempo')"
    )
    equipment_used: list[str] = Field(
        description="Equipment required across all phases (e.g., ['Barbell', 'Dumbbells', 'Cables'])"
    )
    phase_progression_notes: str = Field(
        description="How training changes across phases (e.g., 'Phase 1: 3x12 light, Phase 2: 4x10 moderate, Phase 3: 5x8 heavy')"
    )


class MealPlanMetadata(BaseModel):
    """Plan-level nutrition metadata that applies across all phases."""

    model_config = {"extra": "forbid"}

    dietary_approach: str = Field(
        description="Overall dietary strategy (e.g., 'Flexible dieting', 'Meal prep', 'Intermittent fasting', 'Intuitive eating')"
    )
    macro_strategy: str = Field(
        description="Macronutrient distribution approach (e.g., 'Moderate carb', 'Low carb', 'High protein', 'Carb cycling')"
    )
    meal_timing: str = Field(
        description="Meal timing strategy (e.g., '4 meals evenly spaced', 'Pre/post workout nutrition focus', '16:8 IF window')"
    )
    hydration_guidance: str = Field(
        description="Water intake recommendations (e.g., '0.5-1oz per lb bodyweight', '3-4 liters daily')"
    )
    phase_nutrition_notes: str = Field(
        description="How nutrition changes across phases (e.g., 'Phase 1: 2500 cal, Phase 2: 2800 cal, Phase 3: 3000 cal')"
    )


class PhaseWorkoutDetails(BaseModel):
    """Phase-specific workout implementation details with complete workout definitions."""

    model_config = {"extra": "forbid"}

    workouts: list[WorkoutDay] = Field(
        description="List of distinct workout sessions in this phase. Each workout contains complete exercise prescriptions with sets, reps, instructions, etc.",
        min_length=1
    )
    workout_cycle: list[WorkoutCycleItem] = Field(
        description="Weekly training cycle that references workouts by index. Defines which workout happens on which day, plus rest days. Example: [{'type': 'workout', 'workout_index': 0}, {'type': 'workout', 'workout_index': 1}, {'type': 'rest', 'rest_day': {...}}]"
    )
    intensity_guidance: str = Field(
        description="Intensity guidelines for this phase (e.g., 'RPE 7-8', '70-80% 1RM', 'Moderate intensity')"
    )
    volume_notes: str = Field(
        description="Volume approach for this phase (e.g., '12-15 sets per muscle per week', 'Moderate volume for adaptation')"
    )
    progression_notes: str = Field(
        description="How to progress within this phase (e.g., 'Add 5 lbs per week', 'Increase reps when hitting top range')"
    )


class GroceryItem(BaseModel):
    """A single item to purchase at the grocery store."""

    model_config = {"extra": "forbid"}

    ingredient: str = Field(description="Ingredient name (e.g., 'Chicken breast', 'Brown rice')")
    quantity: str = Field(description="Amount to buy (e.g., '2 lbs', '1 bag', '500g')")
    category: str = Field(
        description="Store category for organization: 'Produce', 'Meat', 'Dairy', 'Grains', 'Frozen', 'Pantry', 'Other'"
    )
    notes: str | None = Field(default=None, description="Shopping notes (e.g., 'boneless, skinless', 'organic preferred')")


class GroceryShoppingScheduleEntry(BaseModel):
    """A single grocery shopping event in the plan.
    
    Uses day_offset from plan start to position events, and repeats_every for frequency.
    This allows any pattern: weekly (7), biweekly (14), every 15 days, irregular, etc.
    
    CRITICAL: day_offset is calculated from phase start day. Count forward from the phase start day of week
    to reach the target day. Example: Phase starts Monday (day 0), Sunday shopping = day_offset 6.
    Phase starts Wednesday, Sunday shopping = day_offset 4 (Wed→Thu→Fri→Sat→Sun).
    """

    model_config = {"extra": "forbid"}

    day_offset: int = Field(
        description="Days from phase start to first occurrence. Count forward from phase start day-of-week to target day. Example: Start Monday, want Sunday = 6. Start Wednesday, want Sunday = 4.",
        ge=0
    )
    time: str = Field(description="Time for shopping (e.g., '10:00 AM', '14:30', '6:00 PM')")
    duration_minutes: int = Field(description="Estimated shopping time in minutes", ge=15, le=180)
    notes: str | None = Field(
        default=None,
        description="Shopping context (e.g., 'Big monthly shop', 'Quick produce run', 'Post-payday stock-up')"
    )
    repeats_every: int | None = Field(
        default=None,
        description="If this event repeats, how many days between occurrences (e.g., 7 for weekly, 14 for biweekly, 15 for every 15 days, None for one-time event)"
    )


class MealPrepSession(BaseModel):
    """A batch meal prep session with cooking instructions."""

    model_config = {"extra": "forbid"}

    session_name: str = Field(description="Prep session name (e.g., 'Sunday Meal Prep', 'Wednesday Batch Cooking')")
    duration_minutes: int = Field(description="Estimated prep time in minutes", ge=30, le=240)
    recipes: list[str] = Field(
        description="Meals being prepped in this session (e.g., ['Grilled Chicken', 'Brown Rice', 'Roasted Vegetables'])"
    )
    batch_size: int = Field(description="Number of servings to prepare", ge=1, le=14)
    instructions: list[str] = Field(
        description="Step-by-step batch cooking instructions (e.g., '1. Preheat oven to 400°F', '2. Season chicken breasts')"
    )
    storage_instructions: str = Field(
        description="How to store prepped food (e.g., 'Divide into 4 containers, refrigerate, use within 4 days')"
    )


class MealPrepScheduleEntry(BaseModel):
    """A single meal prep session in the plan.
    
    Uses day_offset from plan start to position events, and repeats_every for frequency.
    This allows any pattern: weekly (7), every 10 days, twice monthly, irregular, etc.
    
    CRITICAL: day_offset uses same calculation as grocery shopping. Count forward from phase start day-of-week
    to reach target day. Example: Phase starts Monday, Sunday prep = day_offset 6. Phase starts Friday,
    Wednesday prep = day_offset 5 (Fri→Sat→Sun→Mon→Tue→Wed).
    """

    model_config = {"extra": "forbid"}

    day_offset: int = Field(
        description="Days from phase start to first occurrence. Count forward from phase start day-of-week to target day. Same calculation as grocery shopping.",
        ge=0
    )
    time: str = Field(description="Start time (e.g., '14:00', '2:00 PM', '7:30 PM')")
    session_index: int = Field(
        description="Which prep session to execute (index into meal_prep_sessions list)",
        ge=0
    )
    repeats_every: int | None = Field(
        default=None,
        description="Days between repetitions (7 for weekly, 10 for every 10 days, 14 for biweekly, None for one-time event)"
    )
    notes: str | None = Field(
        default=None,
        description="Context (e.g., 'Main weekly prep', 'Phase 1 bulk prep', 'Recovery week light prep', 'Mid-week refresh')"
    )


class PhaseMealDetails(BaseModel):
    """Phase-specific nutrition implementation details."""

    model_config = {"extra": "forbid"}

    daily_calorie_target: int = Field(
        description="Target daily calories for this phase", ge=1200, le=5000
    )
    macro_split: str = Field(
        description="Macronutrient ratio for this phase (e.g., '40% Carbs, 30% Protein, 30% Fat')"
    )
    sample_days: list[DailyMealPlan] = Field(
        description="Sample meal plans for this phase (e.g., training day, rest day)", min_length=1
    )
    phase_nutrition_focus: str = Field(
        description="Nutrition focus for this phase (e.g., 'Metabolic adaptation', 'Muscle building', 'Performance peak', 'Fat loss')"
    )
    grocery_list: list[GroceryItem] = Field(
        default_factory=list,
        description="Complete grocery list for one shopping cycle"
    )
    meal_prep_sessions: list[MealPrepSession] = Field(
        default_factory=list,
        description="Batch meal prep sessions with cooking instructions and storage guidance"
    )
    grocery_shopping_schedule: list[GroceryShoppingScheduleEntry] = Field(
        default_factory=list,
        description=(
            "Explicit grocery shopping schedule with day offsets and repeat patterns. "
            "Examples: Weekly Sunday = [{day_offset: 6, time: '10:00 AM', repeats_every: 7}], "
            "Every 15 days = [{day_offset: 0, time: '2:00 PM', repeats_every: 15}], "
            "Twice monthly = [{day_offset: 0, repeats_every: 30}, {day_offset: 14, repeats_every: 30}]"
        )
    )
    meal_prep_schedule: list[MealPrepScheduleEntry] = Field(
        default_factory=list,
        description=(
            "Explicit meal prep schedule with day offsets and repeat patterns. "
            "Examples: Weekly Sunday = [{day_offset: 6, time: '14:00', session_index: 0, repeats_every: 7}], "
            "Every 10 days = [{day_offset: 2, time: '14:00', session_index: 0, repeats_every: 10}], "
            "Twice weekly = [{day_offset: 0, repeats_every: 7}, {day_offset: 3, repeats_every: 7}]"
        )
    )


class MealPlanOutput(BaseModel):
    """Structured output from Meal Plan Agent."""

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    meal_plan: MealPlan = Field(description="Complete nutrition plan")
    key_foods: list[str] = Field(description="Core foods in the meal plan")
    prep_difficulty: str = Field(description="Overall meal prep difficulty (Easy/Medium/Hard)")


class PhaseOutput(BaseModel):
    """A single phase in a multi-phase fitness plan.
    
    Examples:
    - Bulk Phase + Cut Phase (bodybuilding)
    - Strength Phase + Hypertrophy Phase (powerlifting)
    - Base Building + Peak Performance (endurance)
    - Foundation Phase + Advanced Phase (beginner progression)
    """

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    phase_number: int = Field(description="Phase number in sequence (1, 2, 3, etc.)", ge=1)
    name: str = Field(description="Phase name (e.g., 'Bulk Phase', 'Strength Phase', 'Foundation')")
    objectives: list[str] = Field(
        description="Primary objectives for this phase (e.g., 'Build muscle mass', 'Increase strength')"
    )
    start_date: str = Field(
        description="Phase start date in YYYY-MM-DD format (e.g., '2025-12-15')"
    )
    end_date: str = Field(
        description="Phase end date in YYYY-MM-DD format (e.g., '2026-01-10')"
    )
    duration_weeks: int = Field(
        description="Duration of this phase in weeks (convenience field, derived from dates)", ge=2, le=16
    )
    workout_details: PhaseWorkoutDetails = Field(
        description="Phase-specific workout implementation with training cycle and intensity guidelines"
    )
    meal_details: PhaseMealDetails = Field(
        description="Phase-specific nutrition implementation with calorie targets and meal plans"
    )


class FitnessPlanOutput(BaseModel):
    """Complete fitness plan with one or more phases.

    Single-phase plans: Use 1 phase for straightforward goals
    Multi-phase plans: Use 2+ phases for progressive programs (bulk/cut, beginner/advanced, etc.)
    """

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    goal_summary: str = Field(description="User's primary fitness goal and context")
    start_date: str = Field(
        description="Plan start date in YYYY-MM-DD format (e.g., '2025-12-15')"
    )
    end_date: str = Field(
        description="Plan end date/target date in YYYY-MM-DD format (e.g., '2026-03-15' or race day)"
    )
    duration_weeks: int = Field(
        description="Total program duration in weeks (convenience field, derived from dates)", ge=4, le=52
    )
    fitness_level: str = Field(description="User's fitness level (beginner/intermediate/advanced)")
    workout_metadata: WorkoutPlanMetadata = Field(
        description="High-level workout strategy and principles that apply across all phases"
    )
    meal_metadata: MealPlanMetadata = Field(
        description="High-level nutrition strategy and principles that apply across all phases"
    )
    phases: list[PhaseOutput] = Field(
        description="One or more phases in the program. Each phase has its own workout plan, meal plan, and objectives. Examples: [Bulk Phase, Cut Phase] or [Foundation Phase] for single-phase plans.",
        min_length=1
    )
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
        # Check that we have at least one phase
        if not self.phases:
            raise ValueError("Plan must have at least one phase.")

        # Check total duration matches sum of phase durations
        total_phase_weeks = sum(phase.duration_weeks for phase in self.phases)
        if total_phase_weeks != self.duration_weeks:
            raise ValueError(
                f"Total duration ({self.duration_weeks} weeks) must equal sum of phase durations ({total_phase_weeks} weeks)."
            )
        
        # Validate each phase
        for i, phase in enumerate(self.phases, 1):
            # Check workout cycle exists
            if not phase.workout_details.workout_cycle:
                raise ValueError(f"Phase {i} workout cycle must not be empty.")
            
            # Check meal plan has sample days
            if not phase.meal_details.sample_days:
                raise ValueError(f"Phase {i} meal plan must include at least one sample day.")
            
            # Check calorie target is reasonable
            calories = phase.meal_details.daily_calorie_target
            if not (1200 <= calories <= 5000):
                raise ValueError(
                    f"Phase {i} invalid calorie target: {calories}. Must be 1200-5000."
                )

        return True


class SchedulePreferences(BaseModel):
    """User's schedule preferences for workout and meal planning."""

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    split_type: str = Field(
        default="weekly_fixed",
        description="Training split type: 'weekly_fixed' (same days each week) or 'rolling' (e.g., 4-day cycle repeats regardless of calendar week)",
    )
    preferred_workout_days: list[str] | None = Field(
        default=None,
        description="Preferred days for workouts (e.g., ['Monday', 'Wednesday', 'Friday', 'Saturday']) for weekly_fixed. Leave None for rolling splits.",
    )
    rest_days: list[str] | None = Field(
        default=None,
        description="Mandatory rest days (e.g., ['Sunday']) for weekly_fixed schedules",
    )
    preferred_time: str | None = Field(
        default=None,
        description="Preferred workout time: 'morning' (6-10am), 'afternoon' (12-4pm), 'evening' (5-9pm), or specific time like '6:00 AM'",
    )
    avoid_dates: list[str] | None = Field(
        default=None,
        description="Specific dates to avoid scheduling workouts (e.g., ['2025-12-25', '2026-01-01'] for holidays, travel, events). Format: YYYY-MM-DD",
    )
    notes: str | None = Field(
        default=None, description="Additional scheduling notes, constraints, or preferences"
    )


class ConversationRequirements(BaseModel):
    """Structured requirements extracted from conversation."""

    model_config = {"extra": "forbid"}  # Strict schema for agents SDK

    primary_goal: str = Field(description="Primary fitness goal")
    fitness_level: str = Field(description="Current fitness level")
    workout_frequency: int = Field(description="Days per week for working out", ge=2, le=7)
    equipment_access: str = Field(description="Equipment availability")
    time_per_session: int = Field(
        description="Available time per workout in minutes", ge=20, le=120
    )
    dietary_restrictions: list[str] = Field(
        default_factory=list, description="Dietary restrictions"
    )
    injuries_or_conditions: list[str] = Field(
        default_factory=list, description="Injuries or health conditions"
    )
    schedule_preferences: SchedulePreferences = Field(
        default_factory=SchedulePreferences,
        description="User's scheduling preferences and constraints",
    )
    preferences: str | None = Field(default=None, description="Other preferences or notes")
