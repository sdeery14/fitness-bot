"""Plan service for fitness plan management and persistence."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.fitness_plan import FitnessPlan
from src.models.meal import MealPlan
from src.models.user import User
from src.models.workout import WorkoutPlan


class PlanService:
    """Service for fitness plan operations."""

    async def has_existing_plans(self, user_id: UUID) -> bool:
        """Check if user has any existing fitness plans.

        Args:
            user_id: User's UUID

        Returns:
            True if user has at least one fitness plan (any status), False otherwise
        """
        stmt = select(FitnessPlan).where(FitnessPlan.user_id == user_id).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def __init__(self, db: AsyncSession) -> None:
        """Initialize plan service.

        Args:
            db: Database session for plan queries
        """
        self.db = db

    async def create_plan(
        self,
        user_id: UUID,
        goal: str,
        requirements: dict,
        duration_weeks: int = 12,
        start_date: datetime | None = None,
    ) -> FitnessPlan:
        """Create a new fitness plan.

        Args:
            user_id: User's UUID
            goal: Primary fitness goal
            requirements: User requirements and constraints
            duration_weeks: Plan duration in weeks (default 12)
            start_date: Optional start date (defaults to now)

        Returns:
            Created plan instance

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Create plan
        from datetime import timedelta

        if start_date is None:
            start_date = datetime.now(UTC)
        end_date = start_date + timedelta(weeks=duration_weeks)

        plan = FitnessPlan(
            user_id=user_id,
            goal_type=goal,
            goal_description=requirements.get("goal_description", f"Achieve {goal}"),
            duration_weeks=duration_weeks,
            start_date=start_date,
            end_date=end_date,
            status="active",  # Set to active immediately upon creation

        )

        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)

        return plan

    async def get_plan(self, plan_id: UUID) -> FitnessPlan | None:
        """Retrieve a plan by ID.

        Args:
            plan_id: Plan's UUID

        Returns:
            Plan instance if found, None otherwise
        """
        stmt = select(FitnessPlan).where(FitnessPlan.id == plan_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_plans(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[FitnessPlan]:
        """Retrieve plans for a user.

        Args:
            user_id: User's UUID
            limit: Maximum number of plans to return
            offset: Number of plans to skip

        Returns:
            List of plans ordered by creation date (newest first)
        """
        stmt = (
            select(FitnessPlan)
            .where(FitnessPlan.user_id == user_id)
            .order_by(FitnessPlan.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_plan(self, user_id: UUID) -> FitnessPlan | None:
        """Get the active fitness plan for a user.

        Args:
            user_id: User's UUID

        Returns:
            Active plan if found, None otherwise
        """
        stmt = (
            select(FitnessPlan)
            .where(FitnessPlan.user_id == user_id)
            .where(FitnessPlan.status == "active")
            .order_by(FitnessPlan.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_plan_version(
        self,
        parent_plan_id: UUID,
        version_notes: str | None = None,
    ) -> FitnessPlan:
        """Create a new version of an existing fitness plan.

        This creates a copy of the parent plan with:
        - Incremented version number
        - parent_plan_id pointing to the original
        - 'active' status (parent plan will be marked 'replaced')
        - All related data copied from parent plan

        Args:
            parent_plan_id: UUID of the plan to create a version from
            version_notes: Optional description of what changed

        Returns:
            New plan instance

        Raises:
            ValueError: If parent plan not found
        """
        # Get parent plan
        parent_plan = await self.get_plan(parent_plan_id)
        if not parent_plan:
            raise ValueError(f"Parent plan not found: {parent_plan_id}")

        # Create new plan as a copy
        new_plan = FitnessPlan(
            user_id=parent_plan.user_id,
            goal_type=parent_plan.goal_type,
            goal_description=parent_plan.goal_description,
            target_weight_kg=parent_plan.target_weight_kg,
            target_date=parent_plan.target_date,
            duration_weeks=parent_plan.duration_weeks,
            start_date=parent_plan.start_date,
            end_date=parent_plan.end_date,
            status="active",
            parent_plan_id=parent_plan_id,
            version=parent_plan.version + 1,
            version_notes=version_notes,
        )

        # Mark parent plan as replaced
        parent_plan.status = "replaced"

        # Save both plans
        self.db.add(new_plan)
        await self.db.commit()
        await self.db.refresh(new_plan)
        await self.db.refresh(parent_plan)

        return new_plan

    async def apply_plan_updates(
        self,
        parent_plan_id: UUID,
        updates: list[dict],
        version_notes: str | None = None,
    ) -> FitnessPlan:
        """Apply structured updates to create a new plan version.

        This creates a new plan version with specific field updates applied.
        Supports updates to:
        - Plan-level fields (goal_description, duration_weeks, etc.)
        - Phase fields (phases[0].duration_weeks, phases[1].objectives)
        - Workout fields (workout_plans[0].frequency_per_week)
        - Individual workout fields (phases[0].workouts[1].duration_minutes)
        - Meal plan fields (meal_plans[0].daily_calorie_target)
        - Individual meal fields (phases[0].meals[2].protein_grams)

        Args:
            parent_plan_id: UUID of the plan to update
            updates: List of update operations, each with:
                - field: Field path (e.g., "goal_description", "phases[0].duration_weeks")
                - value: New value to set
                - operation: "set" (default), "append" (for lists), "increment" (for numbers)
            version_notes: Human-readable description of changes

        Returns:
            New plan instance with updates applied

        Raises:
            ValueError: If parent plan not found or invalid update path

        Example updates:
            [
                {"field": "goal_description", "value": "Build muscle and lose 10 lbs", "operation": "set"},
                {"field": "phases[0].duration_weeks", "value": 6, "operation": "set"},
                {"field": "workout_plans[0].frequency_per_week", "value": 4, "operation": "set"},
                {"field": "meal_plans[0].daily_calorie_target", "value": 2200, "operation": "set"}
            ]
        """
        from sqlalchemy.orm import selectinload

        # Load parent plan with all relationships
        stmt = (
            select(FitnessPlan)
            .where(FitnessPlan.id == parent_plan_id)
            .options(
                selectinload(FitnessPlan.phases).selectinload("workouts").selectinload("exercises"),
                selectinload(FitnessPlan.phases).selectinload("meals"),
                selectinload(FitnessPlan.workout_plans),
                selectinload(FitnessPlan.meal_plans),
            )
        )
        result = await self.db.execute(stmt)
        parent_plan = result.scalar_one_or_none()

        if not parent_plan:
            raise ValueError(f"Parent plan not found: {parent_plan_id}")

        # Create new plan version (copy parent)
        new_plan = FitnessPlan(
            user_id=parent_plan.user_id,
            goal_type=parent_plan.goal_type,
            goal_description=parent_plan.goal_description,
            target_weight_kg=parent_plan.target_weight_kg,
            target_date=parent_plan.target_date,
            duration_weeks=parent_plan.duration_weeks,
            start_date=parent_plan.start_date,
            end_date=parent_plan.end_date,
            status="active",
            parent_plan_id=parent_plan_id,
            version=parent_plan.version + 1,
            version_notes=version_notes,
            key_principles=parent_plan.key_principles,
            success_metrics=parent_plan.success_metrics,
            important_notes=parent_plan.important_notes,
        )

        # Apply updates to the new plan
        for update in updates:
            field_path = update.get("field", "")
            value = update.get("value")
            operation = update.get("operation", "set")

            if not field_path:
                continue

            # Parse the field path (e.g., "phases[0].duration_weeks")
            try:
                self._apply_update(new_plan, field_path, value, operation)
            except Exception as e:
                raise ValueError(f"Failed to apply update to '{field_path}': {str(e)}")

        # Mark parent plan as replaced
        parent_plan.status = "replaced"

        # Save both plans
        self.db.add(new_plan)
        await self.db.commit()
        await self.db.refresh(new_plan)
        await self.db.refresh(parent_plan)

        return new_plan

    def _apply_update(
        self,
        obj: object,
        field_path: str,
        value: any,
        operation: str = "set",
    ) -> None:
        """Apply a single update to an object using a field path.

        Args:
            obj: Object to update (FitnessPlan, Phase, Workout, etc.)
            field_path: Dot-separated path with optional array indices
            value: Value to set
            operation: "set", "append", or "increment"

        Raises:
            ValueError: If field path is invalid or operation unsupported
        """
        import re

        # Parse field path: "phases[0].workouts[1].duration_minutes"
        parts = re.split(r'\.|\[|\]', field_path)
        parts = [p for p in parts if p]  # Remove empty strings

        current = obj
        i = 0
        while i < len(parts) - 1:
            part = parts[i]
            
            # Check if next part is an index
            if i + 1 < len(parts) and parts[i + 1].isdigit():
                # Current part is a collection name, next part is index
                collection = getattr(current, part, None)
                if collection is None:
                    raise ValueError(f"Collection '{part}' not found")
                
                index = int(parts[i + 1])
                if index >= len(collection):
                    raise ValueError(f"Index {index} out of range for '{part}' (length {len(collection)})")
                
                current = collection[index]
                i += 2  # Skip both the collection name and the index
            else:
                # Regular attribute access
                current = getattr(current, part, None)
                if current is None:
                    raise ValueError(f"Attribute '{part}' not found")
                i += 1

        # Apply the update to the final field
        final_field = parts[-1]
        
        if operation == "set":
            setattr(current, final_field, value)
        elif operation == "append":
            current_value = getattr(current, final_field, None)
            if not isinstance(current_value, list):
                raise ValueError(f"Cannot append to non-list field '{final_field}'")
            current_value.append(value)
        elif operation == "increment":
            current_value = getattr(current, final_field, 0)
            if not isinstance(current_value, (int, float)):
                raise ValueError(f"Cannot increment non-numeric field '{final_field}'")
            setattr(current, final_field, current_value + value)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def update_plan_status(
        self,
        plan_id: UUID,
        status: str,
        error_message: str | None = None,
    ) -> FitnessPlan | None:
        """Update plan generation status.

        Args:
            plan_id: Plan's UUID
            status: New status (draft, active, completed, abandoned)
            error_message: Optional error message if status is 'failed'

        Returns:
            Updated plan instance if found, None otherwise
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        plan.status = status
        if status == "completed":
            plan.updated_at = datetime.now(UTC)
        # Note: error_message is now logged but not stored in database
        # Consider adding an errors table if error tracking is needed

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def add_workout_plan(
        self,
        plan_id: UUID,
        phase: int,
        week: int,
        workout_data: dict,
    ) -> WorkoutPlan:
        """Add a workout plan to a fitness plan.

        Args:
            plan_id: Parent plan's UUID
            phase: Phase number (1, 2, 3, etc.)
            week: Week number within the overall plan
            workout_data: Workout structure with exercises

        Returns:
            Created workout plan instance

        Raises:
            ValueError: If plan not found
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError("Plan not found")

        workout = WorkoutPlan(
            plan_id=plan_id,
            phase=phase,
            week=week,
            workout_data=workout_data,
        )

        self.db.add(workout)
        await self.db.commit()
        await self.db.refresh(workout)

        return workout

    async def add_meal_plan(
        self,
        plan_id: UUID,
        phase: int,
        week: int,
        meal_data: dict,
    ) -> MealPlan:
        """Add a meal plan to a fitness plan.

        Args:
            plan_id: Parent plan's UUID
            phase: Phase number (1, 2, 3, etc.)
            week: Week number within the overall plan
            meal_data: Meal structure with daily meals

        Returns:
            Created meal plan instance

        Raises:
            ValueError: If plan not found
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError("Plan not found")

        meal = MealPlan(
            plan_id=plan_id,
            phase=phase,
            week=week,
            meal_data=meal_data,
        )

        self.db.add(meal)
        await self.db.commit()
        await self.db.refresh(meal)

        return meal

    def _extract_workouts_from_cycle(self, workout_cycle: list[dict]) -> list[dict]:
        """Extract workout data from training cycle.

        Args:
            workout_cycle: Training cycle with workout and rest day items

        Returns:
            List of workout dictionaries
        """
        workouts = []
        for item in workout_cycle:
            if item.get("type") == "workout":
                workout_index = item.get("workout_index", 0)
                # For now, create basic workout structure
                # The actual workout details should come from the cycle
                workouts.append(
                    {
                        "day_name": f"Workout {workout_index + 1}",
                        "duration_minutes": 60,
                        "focus": "Training",
                        "exercises": [],  # Will be populated from workout_cycle details if available
                    }
                )
        return workouts

    async def get_plan_workouts(self, plan_id: UUID) -> list[WorkoutPlan]:
        """Retrieve all workout plans for a fitness plan.

        Args:
            plan_id: Plan's UUID

        Returns:
            List of workout plans ordered by phase and week
        """
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.plan_id == plan_id)
            .order_by(WorkoutPlan.phase, WorkoutPlan.week)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_plan_meals(self, plan_id: UUID) -> list[MealPlan]:
        """Retrieve all meal plans for a fitness plan.

        Args:
            plan_id: Plan's UUID

        Returns:
            List of meal plans ordered by phase and week
        """
        stmt = (
            select(MealPlan)
            .where(MealPlan.plan_id == plan_id)
            .order_by(MealPlan.phase, MealPlan.week)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save_generated_plan(
        self,
        plan_id: UUID,
        plan_output: dict,
    ) -> FitnessPlan:
        """Save a complete AI-generated fitness plan to the database.

        This method takes the structured output from the AI agent and persists:
        - The full plan snapshot (for reference and regeneration)
        - Individual workout plans with their exercises
        - Individual meal plans with their meals

        Args:
            plan_id: UUID of the plan to update
            plan_output: Dictionary representation of FitnessPlanOutput from AI agent

        Returns:
            Updated FitnessPlan instance

        Raises:
            ValueError: If plan not found
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        # Mark plan as active
        plan.status = "active"

        # Extract plan-level metadata and populate new fields
        plan.key_principles = plan_output.get("key_principles", [])
        plan.success_metrics = plan_output.get("success_metrics", [])
        plan.important_notes = plan_output.get("important_notes")

        # Extract phases from plan output
        phases_data = plan_output.get("phases", [])

        if not phases_data:
            raise ValueError("Plan output must contain phases data")

        # Create ONE workout_plan for the entire fitness plan (not per phase)
        from src.models.workout import WorkoutPlan
        
        workout_metadata = plan_output.get("workout_metadata", {})
        
        # Get workout frequency from requirements dict (passed in plan_output)
        requirements = plan_output.get("requirements", {})
        workout_frequency = requirements.get("workout_plan", {}).get("workout_frequency", 3)
        
        # Get progression strategy from metadata
        progression_strategy_full = workout_metadata.get("progression_strategy", "Progressive overload")
        progression_strategy = (
            progression_strategy_full[:252] + "..."
            if len(progression_strategy_full) > 255
            else progression_strategy_full
        )
        
        workout_plan = WorkoutPlan(
            fitness_plan_id=plan_id,
            frequency_per_week=workout_frequency,
            progression_strategy=progression_strategy,
            phase_progression_notes=workout_metadata.get("phase_progression_notes"),
            equipment_used=workout_metadata.get("equipment_used", []),
            workout_plan_details={
                "program_type": workout_metadata.get("program_type", "General"),
                "progression_strategy": progression_strategy_full,
                "training_principles": workout_metadata.get("training_principles", []),
            },
        )
        self.db.add(workout_plan)
        await self.db.flush()  # Get workout_plan ID
        
        # Create ONE meal_plan for the entire fitness plan (not per phase)
        from src.models.meal import MealPlan
        
        meal_metadata = plan_output.get("meal_metadata", {})
        
        # Get meal frequency from requirements dict (passed in plan_output)
        meal_frequency = requirements.get("meal_plan", {}).get("meal_frequency", 3)
        
        # Use first phase's data to calculate initial calorie/macro targets
        # (these are general guidelines - phase details will have specific values)
        first_phase_meals = phases_data[0].get("meal_details", {}) if phases_data else {}
        daily_calories = first_phase_meals.get("daily_calorie_target", 2000)
        macro_split = first_phase_meals.get("macro_split", "40% Carbs, 30% Protein, 30% Fat")
        
        # Parse macro percentages
        import re
        protein_percent = 30
        carbs_percent = 40
        fats_percent = 30
        
        if "protein" in macro_split.lower():
            protein_match = re.search(r"(\d+)%?\s*protein", macro_split.lower())
            if protein_match:
                protein_percent = int(protein_match.group(1))
        if "carb" in macro_split.lower():
            carbs_match = re.search(r"(\d+)%?\s*carb", macro_split.lower())
            if carbs_match:
                carbs_percent = int(carbs_match.group(1))
        if "fat" in macro_split.lower():
            fats_match = re.search(r"(\d+)%?\s*fat", macro_split.lower())
            if fats_match:
                fats_percent = int(fats_match.group(1))
        
        # Calculate macro grams
        protein_grams = int((daily_calories * protein_percent / 100) / 4)
        carbs_grams = int((daily_calories * carbs_percent / 100) / 4)
        fats_grams = int((daily_calories * fats_percent / 100) / 9)
        
        meal_plan = MealPlan(
            fitness_plan_id=plan_id,
            daily_calorie_target=daily_calories,
            macronutrient_distribution={
                "macro_split": macro_split,
                "protein_percent": protein_percent,
                "carbs_percent": carbs_percent,
                "fats_percent": fats_percent,
            },
            protein_grams_target=protein_grams,
            carbs_grams_target=carbs_grams,
            fats_grams_target=fats_grams,
            meals_per_day=meal_frequency,
            dietary_approach=meal_metadata.get("dietary_approach"),
            macro_strategy=meal_metadata.get("macro_strategy"),
            meal_timing=meal_metadata.get("meal_timing"),
            hydration_guidance=meal_metadata.get("hydration_guidance"),
            phase_nutrition_notes=meal_metadata.get("phase_nutrition_notes"),
        )
        self.db.add(meal_plan)
        await self.db.flush()  # Get meal_plan ID

        # Process each phase
        from datetime import timedelta

        from src.models.fitness_plan import Phase

        current_start_date = plan.start_date

        for phase_data in phases_data:
            phase_number = phase_data.get("phase_number", 1)
            phase_duration = phase_data.get("duration_weeks", plan.duration_weeks)
            phase_end_date = current_start_date + timedelta(weeks=phase_duration)

            # Extract workout details for this phase
            workout_details = phase_data.get("workout_details", {})
            workout_cycle = workout_details.get("workout_cycle", [])

            # Create Phase record with workout_cycle in phase_details
            phase = Phase(
                fitness_plan_id=plan_id,
                phase_number=phase_number,
                name=phase_data.get("name", f"Phase {phase_number}"),
                objectives=phase_data.get("objectives", []),
                start_date=current_start_date,
                end_date=phase_end_date,
                phase_details={
                    "duration_weeks": phase_duration,
                    "workout_cycle": workout_cycle,  # Store for schedule generation
                },
            )
            self.db.add(phase)
            await self.db.flush()  # Flush to get the phase ID

            # Create individual Workout records for this phase (using the shared workout_plan)
            if workout_cycle:
                from src.models.workout import Workout, Exercise

                # Get workouts list from PhaseWorkoutDetails
                workouts_list = workout_details.get("workouts", [])

                for workout_data in workouts_list:
                    # Create Workout record with data from WorkoutDay
                    workout = Workout(
                        workout_plan_id=workout_plan.id,
                        phase_id=phase.id,
                        name=workout_data.get("day_name", "Workout"),
                        workout_type=workout_data.get("workout_type", "strength"),
                        duration_minutes=workout_data.get("duration_minutes", 60),
                        intensity_level=workout_data.get("intensity_level", "moderate"),
                        workout_structure={
                            "warmup": workout_data.get(
                                "warmup", "5-10 minutes of light cardio and dynamic stretching"
                            ),
                            "cooldown": workout_data.get(
                                "cooldown", "5-10 minutes of stretching and mobility"
                            ),
                            "focus": workout_data.get("focus", "General"),
                            "notes": workout_data.get("notes"),
                        },
                    )
                    self.db.add(workout)
                    await self.db.flush()  # Get workout ID for exercises

                    # Create Exercise records for each exercise in this workout
                    exercises_list = workout_data.get("exercises", [])
                    for exercise_order, exercise_data in enumerate(exercises_list, start=1):
                        exercise = Exercise(
                            workout_id=workout.id,
                            exercise_order=exercise_order,
                            name=exercise_data.get("name", "Unknown Exercise"),
                            exercise_type=exercise_data.get("exercise_type", "compound"),
                            target_muscle_groups=exercise_data.get("target_muscle_groups", []),
                            equipment_required=exercise_data.get(
                                "equipment_required", ["bodyweight"]
                            ),
                            sets=exercise_data.get("sets"),
                            reps=exercise_data.get("reps"),
                            duration_seconds=exercise_data.get("duration_seconds"),
                            rest_seconds=exercise_data.get("rest_seconds", 60),
                            tempo=exercise_data.get("tempo"),
                            rpe_target=exercise_data.get("rpe_target"),
                            instructions=exercise_data.get("instructions", ""),
                            form_cues=exercise_data.get("form_cues", []),
                        )
                        self.db.add(exercise)

            # Extract meal details for this phase and create Meal records (using the shared meal_plan)
            meal_details = phase_data.get("meal_details", {})

            if meal_details:
                # Create individual Meal records from sample_days array
                from src.models.meal import Meal

                sample_days = meal_details.get("sample_days", [])

                for day_idx, day_plan in enumerate(sample_days):
                    meals_list = day_plan.get("meals", [])

                    for meal_data in meals_list:
                        # Calculate meal macros from food items
                        foods = meal_data.get("foods", [])
                        meal_protein = sum(food.get("protein_g", 0) for food in foods)
                        meal_carbs = sum(food.get("carbs_g", 0) for food in foods)
                        meal_fat = sum(food.get("fat_g", 0) for food in foods)
                        meal_calories = meal_data.get("total_calories", 0)

                        # Convert foods to ingredients format for frontend
                        ingredients = []
                        for food in foods:
                            ingredients.append(
                                {
                                    "name": food.get("name", "Unknown"),
                                    "quantity": food.get("portion", "1 serving").split()[
                                        0
                                    ],  # Extract number
                                    "unit": " ".join(food.get("portion", "1 serving").split()[1:])
                                    or "serving",  # Extract unit
                                    "calories": food.get("calories", 0),
                                    "protein_grams": food.get("protein_g", 0),
                                    "carbs_grams": food.get("carbs_g", 0),
                                    "fats_grams": food.get("fat_g", 0),
                                }
                            )

                        meal = Meal(
                            meal_plan_id=meal_plan.id,
                            phase_id=phase.id,
                            name=meal_data.get("meal_name", "Meal"),
                            meal_type=meal_data.get("meal_name", "Meal").lower().split()[0]
                            if meal_data.get("meal_name")
                            else "meal",  # Extract first word (breakfast, lunch, etc.)
                            day_of_week=day_idx + 1,  # 1-7 for each sample day
                            calories=meal_calories,
                            protein_grams=meal_protein,
                            carbs_grams=meal_carbs,
                            fats_grams=meal_fat,
                            fiber_grams=0,  # Not provided in current schema
                            meal_details={
                                "ingredients": ingredients,
                                "instructions": [],  # Instructions not provided in current schema
                                "prep_time_minutes": 0,  # Not provided in current schema
                                "cook_time_minutes": 0,  # Not provided in current schema
                                "servings": 1,
                                "notes": meal_data.get("notes", ""),
                            },
                        )
                        self.db.add(meal)

                # Create GroceryShoppingTrip records from grocery_shopping_schedule
                from datetime import time

                from src.models.grocery_trip import GroceryShoppingTrip

                shopping_schedule = meal_details.get("grocery_shopping_schedule", [])
                # Get the phase-level grocery list (shared across all shopping trips in this phase)
                phase_grocery_list = meal_details.get("grocery_list", [])

                for shopping_entry in shopping_schedule:
                    # Parse time if provided
                    entry_time = None
                    time_str = shopping_entry.get("time")
                    if time_str:
                        try:
                            # Parse time string like "09:00" or "9:00 AM"
                            if ":" in time_str:
                                parts = time_str.split(":")
                                hour = int(parts[0])
                                minute = int(parts[1].split()[0])  # Remove AM/PM if present
                                # Convert 12-hour to 24-hour if AM/PM present
                                if "PM" in time_str.upper() and hour != 12:
                                    hour += 12
                                elif "AM" in time_str.upper() and hour == 12:
                                    hour = 0
                                entry_time = time(hour=hour, minute=minute)
                        except (ValueError, IndexError):
                            pass  # Keep as None if parsing fails

                    # Convert grocery list to the format expected by database
                    # Database expects {"items": [...]} but we store just the array
                    items_dict = {"items": phase_grocery_list} if phase_grocery_list else []
                    
                    grocery_trip = GroceryShoppingTrip(
                        phase_id=phase.id,
                        name=shopping_entry.get("name", "Grocery Shopping"),
                        items=items_dict,
                        estimated_duration_minutes=shopping_entry.get(
                            "duration_minutes", 60
                        ),
                        notes=shopping_entry.get("notes"),
                        target_day_name=shopping_entry.get("target_day_name"),
                        time=entry_time,
                        repeats_every=shopping_entry.get("repeats_every"),
                    )
                    self.db.add(grocery_trip)

                # Create MealPrepSession records from meal_prep_schedule
                from src.models.meal_prep import MealPrepSession

                prep_sessions = meal_details.get("meal_prep_sessions", [])
                prep_schedule = meal_details.get("meal_prep_schedule", [])

                for prep_entry in prep_schedule:
                    # Get the session details from meal_prep_sessions using session_index
                    session_index = prep_entry.get("session_index", 0)
                    if session_index < len(prep_sessions):
                        session_details = prep_sessions[session_index]
                    else:
                        # Fallback if index is out of range (shouldn't happen with valid agent output)
                        session_details = {}

                    # Parse time if provided
                    entry_time = None
                    time_str = prep_entry.get("time")
                    if time_str:
                        try:
                            # Parse time string like "18:00" or "6:00 PM"
                            if ":" in time_str:
                                parts = time_str.split(":")
                                hour = int(parts[0])
                                minute = int(parts[1].split()[0])  # Remove AM/PM if present
                                # Convert 12-hour to 24-hour if AM/PM present
                                if "PM" in time_str.upper() and hour != 12:
                                    hour += 12
                                elif "AM" in time_str.upper() and hour == 12:
                                    hour = 0
                                entry_time = time(hour=hour, minute=minute)
                        except (ValueError, IndexError):
                            pass  # Keep as None if parsing fails

                    meal_prep_session = MealPrepSession(
                        phase_id=phase.id,
                        session_name=session_details.get("session_name", "Meal Prep"),
                        recipes=session_details.get("recipes", []),
                        duration_minutes=session_details.get("duration_minutes", 90),
                        batch_size=session_details.get("batch_size", 1),
                        instructions=session_details.get("instructions", []),
                        storage_instructions=session_details.get("storage_instructions"),
                        notes=prep_entry.get("notes"),  # Schedule-level notes
                        target_day_name=prep_entry.get("target_day_name"),
                        time=entry_time,
                        repeats_every=prep_entry.get("repeats_every"),
                    )
                    self.db.add(meal_prep_session)

            # Move to next phase start date
            current_start_date = phase_end_date

        # Commit all changes
        await self.db.commit()
        await self.db.refresh(plan)

        # Automatically create schedule for the entire plan duration
        # This ensures the user's schedule reflects the complete fitness plan
        from src.services.schedule_service import ScheduleService

        schedule_service = ScheduleService(self.db)

        # Check if a schedule already exists for this plan
        from sqlalchemy import select

        from src.models.schedule import Schedule

        existing_schedule_stmt = select(Schedule).where(Schedule.fitness_plan_id == plan_id)
        existing_schedule_result = await self.db.execute(existing_schedule_stmt)
        existing_schedule = existing_schedule_result.scalar_one_or_none()

        if not existing_schedule:
            # Extract schedule preferences from plan requirements
            requirements = plan_output.get("requirements", {})
            schedule_preferences = requirements.get("schedule_preferences", {})

            # Create schedule starting from plan start_date, covering entire duration
            try:
                # Convert datetime to date for schedule service
                schedule_start_date = plan.start_date.date() if isinstance(plan.start_date, datetime) else plan.start_date
                print(f"DEBUG: Creating schedule for plan {plan_id}")
                print(f"DEBUG: plan.start_date type: {type(plan.start_date)}, value: {plan.start_date}")
                print(f"DEBUG: schedule_start_date type: {type(schedule_start_date)}, value: {schedule_start_date}")
                
                await schedule_service.create_schedule(
                    user_id=plan.user_id,
                    fitness_plan_id=plan_id,
                    start_date=schedule_start_date,
                    schedule_preferences=schedule_preferences,
                )
                print(f"DEBUG: Schedule created successfully for plan {plan_id}")
            except Exception as schedule_error:
                # Log the error but don't fail the plan save operation
                import traceback
                print(f"Warning: Failed to auto-create schedule for plan {plan_id}: {schedule_error}")
                print(f"DEBUG: Full traceback:\n{traceback.format_exc()}")

        return plan

    async def analyze_progress_for_suggestions(
        self,
        user_id: UUID,
        fitness_plan_id: UUID,
        days_to_analyze: int = 14,
    ) -> dict:
        """Analyze user progress and generate proactive improvement suggestions.

        Args:
            user_id: User's UUID
            fitness_plan_id: Fitness plan UUID
            days_to_analyze: Number of recent days to analyze (default 14)

        Returns:
            Dictionary with adherence metrics and improvement suggestions
        """
        from datetime import date, timedelta

        from sqlalchemy import and_

        from src.models.schedule import Schedule, ScheduleEntry

        end_date = date.today()
        start_date = end_date - timedelta(days=days_to_analyze)

        # Get recent schedule entries
        stmt = (
            select(ScheduleEntry)
            .join(Schedule)
            .where(
                and_(
                    Schedule.user_id == user_id,
                    Schedule.fitness_plan_id == fitness_plan_id,
                    ScheduleEntry.schedule_date >= start_date,
                    ScheduleEntry.schedule_date <= end_date,
                )
            )
            .order_by(ScheduleEntry.schedule_date)
        )

        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            return {
                "has_data": False,
                "message": "Not enough activity data for analysis",
                "recommendations": [],
            }

        # Calculate metrics
        total_entries = len(entries)
        completed_entries = sum(1 for e in entries if e.completion_status == "completed")
        workout_entries = sum(1 for e in entries if e.workout_id)
        meal_entries = sum(1 for e in entries if e.meal_id)
        completed_workouts = sum(
            1 for e in entries if e.workout_id and e.completion_status == "completed"
        )
        completed_meals = sum(
            1 for e in entries if e.meal_id and e.completion_status == "completed"
        )

        overall_adherence = (completed_entries / total_entries * 100) if total_entries > 0 else 0
        workout_adherence = (
            (completed_workouts / workout_entries * 100) if workout_entries > 0 else 0
        )
        meal_adherence = (completed_meals / meal_entries * 100) if meal_entries > 0 else 0

        # Analyze patterns by day of week
        from collections import defaultdict

        day_stats = defaultdict(lambda: {"total": 0, "completed": 0})
        for entry in entries:
            day_name = entry.schedule_date.strftime("%A")
            day_stats[day_name]["total"] += 1
            if entry.completion_status == "completed":
                day_stats[day_name]["completed"] += 1

        weak_days = []
        for day, stats in day_stats.items():
            day_rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            if day_rate < 70:
                weak_days.append({"day": day, "adherence_rate": round(day_rate, 1)})

        return {
            "has_data": True,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "adherence_metrics": {
                "overall": round(overall_adherence, 1),
                "workouts": round(workout_adherence, 1),
                "meals": round(meal_adherence, 1),
            },
            "activity_counts": {
                "total": total_entries,
                "completed": completed_entries,
                "workouts_completed": completed_workouts,
                "meals_completed": completed_meals,
            },
            "patterns": {
                "weak_days": weak_days,
            },
        }

    async def generate_improvement_recommendations(
        self,
        user_id: UUID,
        fitness_plan_id: UUID,
    ) -> dict:
        """Generate personalized improvement recommendations based on adherence analysis.

        Args:
            user_id: User's UUID
            fitness_plan_id: Fitness plan UUID

        Returns:
            Dictionary with prioritized recommendations
        """
        # Get analysis data
        analysis = await self.analyze_progress_for_suggestions(user_id, fitness_plan_id)

        if not analysis["has_data"]:
            return {
                "recommendations": [],
                "message": "Complete activities for at least 2 weeks to receive personalized recommendations",
            }

        adherence = analysis["adherence_metrics"]
        patterns = analysis["patterns"]
        recommendations = []

        # Low overall adherence
        if adherence["overall"] < 50:
            recommendations.append(
                {
                    "category": "Schedule Simplification",
                    "priority": "high",
                    "title": "Simplify Your Schedule",
                    "description": f"Your current adherence is {adherence['overall']:.0f}%. "
                    "Consider reducing workout frequency to build consistency.",
                    "action_items": [
                        "Reduce weekly workouts by 1-2 sessions",
                        "Focus on quality over quantity",
                        "Build a sustainable habit first",
                    ],
                    "expected_impact": "Improved consistency and motivation",
                }
            )

        # Moderate adherence
        elif adherence["overall"] < 70:
            recommendations.append(
                {
                    "category": "Flexibility & Options",
                    "priority": "medium",
                    "title": "Add Flexible Alternatives",
                    "description": f"You're at {adherence['overall']:.0f}% adherence. "
                    "Adding flexible options can help you hit your targets more consistently.",
                    "action_items": [
                        "Add shorter workout alternatives for busy days",
                        "Include home workout options when gym access is limited",
                        "Allow meal swaps for similar macros",
                    ],
                    "expected_impact": "Better adherence on challenging days",
                }
            )

        # Strong adherence - ready for progression
        elif adherence["overall"] >= 80:
            recommendations.append(
                {
                    "category": "Progressive Overload",
                    "priority": "medium",
                    "title": "Time to Level Up",
                    "description": f"Excellent {adherence['overall']:.0f}% adherence! "
                    "You're ready to increase workout intensity.",
                    "action_items": [
                        "Increase weights by 5-10%",
                        "Add 1-2 reps per set",
                        "Consider adding an extra training session",
                    ],
                    "expected_impact": "Continued progress and adaptation",
                }
            )

        # Workout vs meal disparity
        if abs(adherence["workouts"] - adherence["meals"]) > 20:
            if adherence["workouts"] < adherence["meals"]:
                recommendations.append(
                    {
                        "category": "Workout Optimization",
                        "priority": "high",
                        "title": "Make Workouts More Accessible",
                        "description": f"Workout adherence ({adherence['workouts']:.0f}%) is notably lower than "
                        f"meal adherence ({adherence['meals']:.0f}%).",
                        "action_items": [
                            "Shorten workout duration",
                            "Add bodyweight alternatives",
                            "Schedule workouts at more convenient times",
                        ],
                        "expected_impact": "Balanced adherence across all activities",
                    }
                )
            else:
                recommendations.append(
                    {
                        "category": "Nutrition Planning",
                        "priority": "high",
                        "title": "Simplify Meal Planning",
                        "description": f"Meal adherence ({adherence['meals']:.0f}%) is notably lower than "
                        f"workout adherence ({adherence['workouts']:.0f}%).",
                        "action_items": [
                            "Batch cook meals for the week",
                            "Use simpler recipes",
                            "Allow more flexible meal options",
                        ],
                        "expected_impact": "Improved nutrition consistency",
                    }
                )

        # Weak days pattern
        if patterns["weak_days"]:
            weak_day_names = ", ".join([d["day"] for d in patterns["weak_days"]])
            recommendations.append(
                {
                    "category": "Schedule Optimization",
                    "priority": "medium",
                    "title": f"Address {weak_day_names} Challenges",
                    "description": f"Your adherence is consistently lower on {weak_day_names}.",
                    "action_items": [
                        f"Identify specific barriers on {weak_day_names}",
                        "Consider lighter activities on these days",
                        "Prepare in advance to reduce friction",
                    ],
                    "expected_impact": "More consistent week-to-week adherence",
                }
            )

        # Get plan details for duration-based recommendations
        plan = await self.get_plan(fitness_plan_id)
        if plan and plan.start_date:
            from datetime import date

            days_active = (date.today() - plan.start_date).days
            if days_active >= 30 and adherence["overall"] >= 75:
                recommendations.append(
                    {
                        "category": "Goal Expansion",
                        "priority": "low",
                        "title": "Consider New Challenges",
                        "description": f"You've maintained strong adherence for {days_active} days!",
                        "action_items": [
                            "Add flexibility or mobility work",
                            "Incorporate skill-based training",
                            "Set a new performance goal",
                        ],
                        "expected_impact": "Sustained motivation and continued growth",
                    }
                )

        return {
            "user_id": str(user_id),
            "fitness_plan_id": str(fitness_plan_id),
            "analysis_summary": {
                "overall_adherence": adherence["overall"],
                "workout_adherence": adherence["workouts"],
                "meal_adherence": adherence["meals"],
            },
            "recommendations": recommendations,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def check_phase_completion(
        self,
        fitness_plan_id: UUID,
    ) -> dict:
        """Check if current phase objectives are met and if transition is needed.

        Args:
            fitness_plan_id: Plan's UUID

        Returns:
            Dictionary with phase completion status and details

        Logic:
            - Identifies current active phase based on current date
            - Checks phase objectives completion criteria
            - Returns transition readiness and next phase details
        """
        from datetime import date

        from src.models.fitness_plan import Phase

        # Get plan with phases
        plan = await self.get_plan(fitness_plan_id)
        if not plan:
            raise ValueError(f"Plan {fitness_plan_id} not found")

        # Get all phases ordered by phase_number
        stmt = (
            select(Phase)
            .where(Phase.fitness_plan_id == fitness_plan_id)
            .order_by(Phase.phase_number)
        )
        result = await self.db.execute(stmt)
        phases = list(result.scalars().all())

        if not phases:
            return {
                "has_phases": False,
                "current_phase": None,
                "is_complete": False,
                "should_transition": False,
            }

        # Determine current phase based on date
        today = date.today()
        current_phase = None
        next_phase = None

        for i, phase in enumerate(phases):
            phase_start = phase.start_date.date() if phase.start_date else None
            phase_end = phase.end_date.date() if phase.end_date else None

            if phase_start and phase_end and phase_start <= today <= phase_end:
                current_phase = phase
                if i + 1 < len(phases):
                    next_phase = phases[i + 1]
                break

        if not current_phase:
            # Check if we're past all phases
            last_phase = phases[-1]
            last_end = last_phase.end_date.date() if last_phase.end_date else None
            if last_end and today > last_end:
                return {
                    "has_phases": True,
                    "current_phase": None,
                    "all_phases_complete": True,
                    "is_complete": True,
                    "should_transition": False,
                }

            # Not yet started
            return {
                "has_phases": True,
                "current_phase": None,
                "is_complete": False,
                "should_transition": False,
            }

        # Check if current phase end date is approaching or past
        phase_end = current_phase.end_date.date()
        days_until_end = (phase_end - today).days

        # Phase is complete if we're within 2 days of end or past it
        is_complete = days_until_end <= 2
        should_transition = is_complete and next_phase is not None

        return {
            "has_phases": True,
            "current_phase": {
                "id": str(current_phase.id),
                "phase_number": current_phase.phase_number,
                "name": current_phase.name,
                "objectives": current_phase.objectives,
                "start_date": current_phase.start_date.isoformat(),
                "end_date": current_phase.end_date.isoformat(),
                "days_remaining": max(0, days_until_end),
            },
            "next_phase": {
                "id": str(next_phase.id),
                "phase_number": next_phase.phase_number,
                "name": next_phase.name,
                "objectives": next_phase.objectives,
                "start_date": next_phase.start_date.isoformat(),
                "end_date": next_phase.end_date.isoformat(),
            }
            if next_phase
            else None,
            "is_complete": is_complete,
            "should_transition": should_transition,
        }

    async def transition_to_next_phase(
        self,
        fitness_plan_id: UUID,
        trigger_reason: str = "automatic",
    ) -> dict:
        """Transition fitness plan to the next phase.

        Args:
            fitness_plan_id: Plan's UUID
            trigger_reason: Reason for transition (automatic, manual, milestone)

        Returns:
            Dictionary with transition results and new phase details

        Raises:
            ValueError: If plan not found or no next phase available
        """
        # Check phase completion status
        phase_status = await self.check_phase_completion(fitness_plan_id)

        if not phase_status["has_phases"]:
            raise ValueError("Plan does not have multiple phases")

        if not phase_status["should_transition"]:
            if phase_status.get("all_phases_complete"):
                raise ValueError("All phases are already complete")
            else:
                raise ValueError("Current phase is not ready for transition")

        current_phase = phase_status["current_phase"]
        next_phase = phase_status["next_phase"]

        if not next_phase:
            raise ValueError("No next phase available for transition")

        # TODO: Consider adding a PhaseTransition table for historical tracking if needed
        plan = await self.get_plan(fitness_plan_id)
        await self.db.commit()
        await self.db.refresh(plan)

        return {
            "success": True,
            "transition": {
                "from_phase": current_phase,
                "to_phase": next_phase,
                "trigger_reason": trigger_reason,
                "transitioned_at": datetime.now(UTC).isoformat(),
            },
            "message": f"Successfully transitioned from {current_phase['name']} to {next_phase['name']}",
        }
