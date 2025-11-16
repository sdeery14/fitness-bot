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
            plan_snapshot={},  # Initialize empty, will be populated when plan is generated
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
        elif error_message:
            # Store error in plan_snapshot if it exists, otherwise create it
            if plan.plan_snapshot:
                plan.plan_snapshot = {
                    **plan.plan_snapshot,
                    "error": error_message,
                }
            else:
                plan.plan_snapshot = {"error": error_message}

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

        # Save the complete plan snapshot
        plan.plan_snapshot = plan_output
        plan.status = "active"

        # Extract workout plan data
        workout_plan_data = plan_output.get("workout_plan", {})
        if workout_plan_data:
            # Create a WorkoutPlan record for the entire program
            workout_plan = WorkoutPlan(
                fitness_plan_id=plan_id,
                frequency_per_week=workout_plan_data.get("frequency_per_week", 3),
                progression_strategy=workout_plan_data.get("progression_notes", "Progressive overload"),
                workout_plan_details={
                    "program_type": workout_plan_data.get("program_type", "General"),
                    "duration_weeks": workout_plan_data.get("duration_weeks", plan.duration_weeks),
                    "workouts": workout_plan_data.get("workouts", []),
                },
            )
            self.db.add(workout_plan)

        # Extract meal plan data
        meal_plan_data = plan_output.get("meal_plan", {})
        if meal_plan_data:
            # Parse macro split to calculate individual macro targets
            daily_calories = meal_plan_data.get("daily_calorie_target", 2000)
            macro_split = meal_plan_data.get("macro_split", "40% Carbs, 30% Protein, 30% Fat")

            # Extract percentages from macro split string
            # Default to 40/30/30 (carbs/protein/fat) if parsing fails
            protein_percent = 30
            carbs_percent = 40
            fats_percent = 30

            # Try to parse the macro split
            import re
            if "protein" in macro_split.lower():
                protein_match = re.search(r'(\d+)%?\s*protein', macro_split.lower())
                if protein_match:
                    protein_percent = int(protein_match.group(1))
            if "carb" in macro_split.lower():
                carbs_match = re.search(r'(\d+)%?\s*carb', macro_split.lower())
                if carbs_match:
                    carbs_percent = int(carbs_match.group(1))
            if "fat" in macro_split.lower():
                fats_match = re.search(r'(\d+)%?\s*fat', macro_split.lower())
                if fats_match:
                    fats_percent = int(fats_match.group(1))

            # Calculate macro grams (protein: 4 cal/g, carbs: 4 cal/g, fats: 9 cal/g)
            protein_grams = int((daily_calories * protein_percent / 100) / 4)
            carbs_grams = int((daily_calories * carbs_percent / 100) / 4)
            fats_grams = int((daily_calories * fats_percent / 100) / 9)

            # Create a MealPlan record for the entire program
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
                meals_per_day=meal_plan_data.get("meal_frequency", 3),
            )
            self.db.add(meal_plan)

        # Commit all changes
        await self.db.commit()
        await self.db.refresh(plan)

        return plan
