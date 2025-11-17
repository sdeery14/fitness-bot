"""Schedule service for managing daily workout and meal schedules."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.fitness_plan import FitnessPlan
from src.models.meal import Meal
from src.models.schedule import Schedule, ScheduleEntry
from src.models.workout import Workout


class ScheduleService:
    """Service for schedule operations and completion tracking."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize schedule service.

        Args:
            db: Database session for schedule queries
        """
        self.db = db

    async def create_schedule(
        self,
        user_id: UUID,
        fitness_plan_id: UUID,
        start_date: date | None = None,
    ) -> Schedule:
        """Create a new schedule for a fitness plan.

        Generates schedule entries for all workouts and meals in the plan,
        distributed across the plan duration.

        Args:
            user_id: User's UUID
            fitness_plan_id: FitnessPlan's UUID
            start_date: Optional start date (defaults to today)

        Returns:
            Created schedule with entries

        Raises:
            ValueError: If plan not found or already has a schedule
        """
        # Check if schedule already exists for this plan
        existing_stmt = select(Schedule).where(Schedule.fitness_plan_id == fitness_plan_id)
        existing_result = await self.db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise ValueError("Schedule already exists for this plan")

        # Load the fitness plan with related workouts and meals
        # Note: FitnessPlan has workout_plans and meal_plans (plural) relationships
        stmt = (
            select(FitnessPlan)
            .where(FitnessPlan.id == fitness_plan_id)
            .options(
                selectinload(FitnessPlan.phases),
            )
        )
        result = await self.db.execute(stmt)
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError("Fitness plan not found")

        # Create schedule
        if start_date is None:
            start_date = date.today()

        schedule = Schedule(
            user_id=user_id,
            fitness_plan_id=fitness_plan_id,
            start_date=start_date,
            last_recalculated_at=datetime.now(UTC),
            recalculation_reason="Initial schedule creation",
        )
        self.db.add(schedule)
        await self.db.flush()  # Get schedule.id

        # Load workouts for this plan
        workouts_stmt = select(Workout).join(Workout.workout_plan).where(
            Workout.workout_plan.has(fitness_plan_id=fitness_plan_id)
        )
        workouts_result = await self.db.execute(workouts_stmt)
        workouts = list(workouts_result.scalars().all())

        # Load meals for this plan
        meals_stmt = select(Meal).join(Meal.meal_plan).where(
            Meal.meal_plan.has(fitness_plan_id=fitness_plan_id)
        )
        meals_result = await self.db.execute(meals_stmt)
        meals = list(meals_result.scalars().all())

        # Generate schedule entries for workouts
        if workouts:
            await self._generate_workout_entries(
                schedule=schedule,
                workouts=workouts,
                start_date=start_date,
                duration_weeks=plan.duration_weeks,
            )

        # Generate schedule entries for meals
        if meals:
            await self._generate_meal_entries(
                schedule=schedule,
                meals=meals,
                start_date=start_date,
                duration_weeks=plan.duration_weeks,
            )

        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def _generate_workout_entries(
        self,
        schedule: Schedule,
        workouts: list[Workout],
        start_date: date,
        duration_weeks: int,
    ) -> None:
        """Generate schedule entries for workouts.

        Distributes workouts across the week based on their phase assignment.

        Args:
            schedule: Schedule to add entries to
            workouts: List of workouts from the plan
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
        """
        # Group workouts by phase
        workouts_by_phase: dict[UUID | None, list[Workout]] = {}
        for workout in workouts:
            phase_id = workout.phase_id
            if phase_id not in workouts_by_phase:
                workouts_by_phase[phase_id] = []
            workouts_by_phase[phase_id].append(workout)

        # For each phase, schedule workouts evenly throughout the phase duration
        for _phase_id, phase_workouts in workouts_by_phase.items():
            if not phase_workouts:
                continue

            # Default to full plan duration if no phase info
            phase_start = start_date
            phase_weeks = duration_weeks

            # If phase exists, use its dates (would need to load phase info)
            # For now, distribute evenly across entire plan

            # Schedule each workout type on different days of the week
            days_between_workouts = 2  # Default spacing
            for idx, workout in enumerate(phase_workouts):
                # Calculate which day of the week this workout should occur
                day_offset = idx * days_between_workouts

                # Repeat weekly throughout the phase
                current_date = phase_start + timedelta(days=day_offset)
                end_date = phase_start + timedelta(weeks=phase_weeks)

                while current_date < end_date:
                    entry = ScheduleEntry(
                        schedule_id=schedule.id,
                        entry_type="workout",
                        entry_date=current_date,
                        entry_time=None,  # User can set their preferred time
                        workout_id=workout.id,
                        meal_id=None,
                        completion_status="scheduled",
                    )
                    self.db.add(entry)
                    current_date += timedelta(weeks=1)  # Repeat weekly

    async def _generate_meal_entries(
        self,
        schedule: Schedule,
        meals: list[Meal],
        start_date: date,
        duration_weeks: int,
    ) -> None:
        """Generate schedule entries for meals.

        Creates daily meal entries for the entire plan duration.

        Args:
            schedule: Schedule to add entries to
            meals: List of meals from the plan
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
        """
        end_date = start_date + timedelta(weeks=duration_weeks)

        # Meal timing defaults
        meal_times = {
            "breakfast": time(8, 0),
            "lunch": time(12, 0),
            "dinner": time(18, 0),
            "snack": time(15, 0),
        }

        # Group meals by type
        meals_by_type: dict[str, list[Meal]] = {}
        for meal in meals:
            meal_type = meal.meal_type
            if meal_type not in meals_by_type:
                meals_by_type[meal_type] = []
            meals_by_type[meal_type].append(meal)

        # Create daily entries for each meal type
        current_date = start_date
        meal_rotation_index = {meal_type: 0 for meal_type in meals_by_type}

        while current_date < end_date:
            for meal_type, meal_list in meals_by_type.items():
                if not meal_list:
                    continue

                # Rotate through available meals for this type
                idx = meal_rotation_index[meal_type] % len(meal_list)
                meal = meal_list[idx]

                entry = ScheduleEntry(
                    schedule_id=schedule.id,
                    entry_type="meal",
                    entry_date=current_date,
                    entry_time=meal_times.get(meal_type.lower(), time(12, 0)),
                    workout_id=None,
                    meal_id=meal.id,
                    completion_status="scheduled",
                )
                self.db.add(entry)

                meal_rotation_index[meal_type] += 1

            current_date += timedelta(days=1)

    async def get_today_schedule(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> list[ScheduleEntry]:
        """Get schedule entries for today (or specified date).

        Args:
            user_id: User's UUID
            target_date: Optional date (defaults to today)

        Returns:
            List of schedule entries for the date
        """
        if target_date is None:
            target_date = date.today()

        stmt = (
            select(ScheduleEntry)
            .join(Schedule)
            .where(
                and_(
                    Schedule.user_id == user_id,
                    ScheduleEntry.entry_date == target_date,
                )
            )
            .options(
                selectinload(ScheduleEntry.workout),
                selectinload(ScheduleEntry.meal),
            )
            .order_by(ScheduleEntry.entry_time, ScheduleEntry.entry_type)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming_schedule(
        self,
        user_id: UUID,
        days: int = 14,
        start_date: date | None = None,
    ) -> list[ScheduleEntry]:
        """Get schedule entries for the next N days.

        Args:
            user_id: User's UUID
            days: Number of days to look ahead (default 14)
            start_date: Optional start date (defaults to today)

        Returns:
            List of schedule entries ordered by date and time
        """
        if start_date is None:
            start_date = date.today()

        end_date = start_date + timedelta(days=days)

        stmt = (
            select(ScheduleEntry)
            .join(Schedule)
            .where(
                and_(
                    Schedule.user_id == user_id,
                    ScheduleEntry.entry_date >= start_date,
                    ScheduleEntry.entry_date < end_date,
                )
            )
            .options(
                selectinload(ScheduleEntry.workout),
                selectinload(ScheduleEntry.meal),
            )
            .order_by(ScheduleEntry.entry_date, ScheduleEntry.entry_time, ScheduleEntry.entry_type)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_entry_complete(
        self,
        entry_id: UUID,
        user_notes: str | None = None,
    ) -> ScheduleEntry:
        """Mark a schedule entry as completed.

        Args:
            entry_id: ScheduleEntry's UUID
            user_notes: Optional user notes about completion

        Returns:
            Updated schedule entry

        Raises:
            ValueError: If entry not found
        """
        stmt = select(ScheduleEntry).where(ScheduleEntry.id == entry_id)
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            raise ValueError("Schedule entry not found")

        entry.completion_status = "completed"
        entry.completed_at = datetime.now(UTC)
        if user_notes:
            entry.user_notes = user_notes

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def mark_entry_skipped(
        self,
        entry_id: UUID,
        skipped_reason: str | None = None,
    ) -> ScheduleEntry:
        """Mark a schedule entry as skipped.

        Args:
            entry_id: ScheduleEntry's UUID
            skipped_reason: Optional reason for skipping

        Returns:
            Updated schedule entry

        Raises:
            ValueError: If entry not found
        """
        stmt = select(ScheduleEntry).where(ScheduleEntry.id == entry_id)
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            raise ValueError("Schedule entry not found")

        entry.completion_status = "skipped"
        entry.completed_at = datetime.now(UTC)
        if skipped_reason:
            entry.skipped_reason = skipped_reason

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def advance_schedule(
        self,
        schedule_id: UUID,
        days_to_advance: int,
        reason: str | None = None,
    ) -> Schedule:
        """Advance all incomplete schedule entries by a number of days.

        Used for rescheduling after disruptions or extended breaks.

        Args:
            schedule_id: Schedule's UUID
            days_to_advance: Number of days to push forward
            reason: Optional reason for advancement

        Returns:
            Updated schedule

        Raises:
            ValueError: If schedule not found
        """
        stmt = select(Schedule).where(Schedule.id == schedule_id)
        result = await self.db.execute(stmt)
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        # Update all incomplete entries
        update_stmt = (
            select(ScheduleEntry)
            .where(
                and_(
                    ScheduleEntry.schedule_id == schedule_id,
                    ScheduleEntry.completion_status.in_(["scheduled", "rescheduled"]),
                )
            )
        )
        update_result = await self.db.execute(update_stmt)
        entries = update_result.scalars().all()

        for entry in entries:
            entry.entry_date = entry.entry_date + timedelta(days=days_to_advance)
            entry.completion_status = "rescheduled"

        # Update schedule metadata
        schedule.last_recalculated_at = datetime.now(UTC)
        schedule.recalculation_reason = reason or f"Advanced by {days_to_advance} days"

        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule
