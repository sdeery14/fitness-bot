"""Schedule service for managing daily workout and meal schedules."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.conversation import DisruptionEvent
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
        schedule_preferences: dict | None = None,
    ) -> Schedule:
        """Create a new schedule for a fitness plan with user preferences.

        Generates schedule entries for all workouts and meals in the plan,
        distributed according to user's scheduling preferences (weekly fixed
        vs rolling split, preferred days, rest days, avoid dates, etc.).

        Args:
            user_id: User's UUID
            fitness_plan_id: FitnessPlan's UUID
            start_date: Optional start date (defaults to today)
            schedule_preferences: User's scheduling preferences dict with:
                - split_type: 'weekly_fixed' or 'rolling'
                - preferred_workout_days: list of day names for weekly_fixed
                - rest_days: list of mandatory rest day names
                - preferred_time: workout time preference
                - avoid_dates: list of dates to skip (YYYY-MM-DD format)
                - notes: additional scheduling notes

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

        if schedule_preferences is None:
            schedule_preferences = {}

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
        workouts_stmt = (
            select(Workout)
            .join(Workout.workout_plan)
            .where(Workout.workout_plan.has(fitness_plan_id=fitness_plan_id))
        )
        workouts_result = await self.db.execute(workouts_stmt)
        workouts = list(workouts_result.scalars().all())

        # Load meals for this plan
        meals_stmt = (
            select(Meal)
            .join(Meal.meal_plan)
            .where(Meal.meal_plan.has(fitness_plan_id=fitness_plan_id))
        )
        meals_result = await self.db.execute(meals_stmt)
        meals = list(meals_result.scalars().all())

        # Generate schedule entries for workouts using training cycle from plan_snapshot
        if workouts:
            # Extract training_cycle from plan_snapshot if available
            training_cycle = None
            if plan.plan_snapshot:
                # Try new schema structure first (phases with workout_details)
                phases = (
                    plan.plan_snapshot.get("phases")
                    if isinstance(plan.plan_snapshot, dict)
                    else None
                )
                if phases and isinstance(phases, list) and len(phases) > 0:
                    # Use the first phase's workout cycle for now
                    # TODO: Handle multi-phase scheduling properly
                    workout_details = (
                        phases[0].get("workout_details", {}) if isinstance(phases[0], dict) else {}
                    )
                    training_cycle = (
                        workout_details.get("workout_cycle")
                        if isinstance(workout_details, dict)
                        else None
                    )

            if training_cycle:
                # Use explicit training cycle from AI agent
                await self._generate_cycle_based_entries(
                    schedule=schedule,
                    workouts=workouts,
                    training_cycle=training_cycle,
                    start_date=start_date,
                    duration_weeks=plan.duration_weeks,
                    preferences=schedule_preferences,
                )
            else:
                # Fallback to legacy behavior if no training_cycle provided
                split_type = schedule_preferences.get("split_type", "weekly_fixed")

                if split_type == "rolling":
                    await self._generate_rolling_split_entries(
                        schedule=schedule,
                        workouts=workouts,
                        start_date=start_date,
                        duration_weeks=plan.duration_weeks,
                        preferences=schedule_preferences,
                    )
                else:
                    await self._generate_weekly_fixed_entries(
                        schedule=schedule,
                        workouts=workouts,
                        start_date=start_date,
                        duration_weeks=plan.duration_weeks,
                        preferences=schedule_preferences,
                    )

        # Generate schedule entries for meals
        if meals:
            await self._generate_meal_entries(
                schedule=schedule,
                meals=meals,
                start_date=start_date,
                duration_weeks=plan.duration_weeks,
            )

        # Generate grocery shopping entries
        await self._generate_grocery_shopping_entries(
            schedule=schedule,
            fitness_plan=plan,
            start_date=start_date,
            duration_weeks=plan.duration_weeks,
            preferences=schedule_preferences,
        )

        # Generate meal prep entries
        await self._generate_meal_prep_entries(
            schedule=schedule,
            fitness_plan=plan,
            start_date=start_date,
            duration_weeks=plan.duration_weeks,
            preferences=schedule_preferences,
        )

        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def _generate_weekly_fixed_entries(
        self,
        schedule: Schedule,
        workouts: list[Workout],
        start_date: date,
        duration_weeks: int,
        preferences: dict | None,
    ) -> None:
        """Generate weekly fixed schedule (same days each week).

        Assigns each workout to specific days of the week based on user preferences.
        Workouts repeat on the same day each week throughout the plan duration.

        Args:
            schedule: Schedule to add entries to
            workouts: List of workouts from the plan
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
            preferences: User scheduling preferences dict
        """
        # Calculate plan end date
        plan_end_date = start_date + timedelta(weeks=duration_weeks)

        # Get user preferences
        preferred_days = preferences.get("preferred_workout_days", []) if preferences else []
        rest_days = preferences.get("rest_days", []) if preferences else []
        avoid_dates = preferences.get("avoid_dates", []) if preferences else []
        preferred_time = self._parse_preferred_time(preferences)

        # Day name to weekday offset mapping
        day_name_to_offset = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        # Create workout-to-day mapping
        workout_schedule = {}
        if preferred_days:
            # User specified preferred days - assign workouts to these days
            for i, workout in enumerate(workouts):
                day_name = preferred_days[i % len(preferred_days)]
                workout_schedule[workout.id] = day_name_to_offset.get(day_name.lower(), i % 7)
        else:
            # Auto-distribute workouts evenly across the week
            num_workouts = len(workouts)
            if num_workouts > 0:
                days_between = 7 // num_workouts if num_workouts <= 7 else 1
                for i, workout in enumerate(workouts):
                    workout_schedule[workout.id] = (i * days_between) % 7

        # Generate entries for each workout on its assigned day
        for workout in workouts:
            day_offset = workout_schedule[workout.id]

            # Find first occurrence of this day of week
            current_date = start_date
            while current_date.weekday() != day_offset:
                current_date += timedelta(days=1)

            # Repeat weekly until plan end
            while current_date <= plan_end_date:
                # Skip if it's a rest day or avoid date
                day_name = current_date.strftime("%A").lower()
                date_str = current_date.isoformat()

                if day_name not in [d.lower() for d in rest_days] and date_str not in avoid_dates:
                    entry = ScheduleEntry(
                        schedule_id=schedule.id,
                        entry_type="workout",
                        entry_date=current_date,
                        entry_time=preferred_time,
                        workout_id=workout.id,
                        meal_id=None,
                        completion_status="scheduled",
                    )
                    self.db.add(entry)

                current_date += timedelta(weeks=1)

        # Commit all schedule entries
        await self.db.flush()

    async def _generate_rolling_split_entries(
        self,
        schedule: Schedule,
        workouts: list[Workout],
        start_date: date,
        duration_weeks: int,
        preferences: dict | None,
    ) -> None:
        """Generate rolling split schedule (e.g., 4-day cycle repeats regardless of week).

        Workouts cycle through in order, independent of calendar weeks.
        For example, a 4-day split continues: Day1, Day2, Day3, Day4, Day1, Day2...
        This is useful for powerlifting programs or when weekly structure isn't needed.

        Args:
            schedule: Schedule to add entries to
            workouts: List of workouts from the plan
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
            preferences: User scheduling preferences dict
        """
        # Calculate plan end date
        plan_end_date = start_date + timedelta(weeks=duration_weeks)

        # Get user preferences
        rest_days_of_week = preferences.get("rest_days", []) if preferences else []
        avoid_dates = preferences.get("avoid_dates", []) if preferences else []
        preferred_time = self._parse_preferred_time(preferences)

        # Start rolling through workouts
        current_date = start_date
        workout_idx = 0

        while current_date <= plan_end_date:
            # Check if current date should be skipped
            day_name = current_date.strftime("%A").lower()
            date_str = current_date.isoformat()

            # Skip rest days and avoid dates
            if day_name in [d.lower() for d in rest_days_of_week] or date_str in avoid_dates:
                current_date += timedelta(days=1)
                continue

            # Assign next workout in rotation
            workout = workouts[workout_idx % len(workouts)]

            entry = ScheduleEntry(
                schedule_id=schedule.id,
                entry_type="workout",
                entry_date=current_date,
                entry_time=preferred_time,
                workout_id=workout.id,
                meal_id=None,
                completion_status="scheduled",
            )
            self.db.add(entry)

            # Move to next workout and next day
            workout_idx += 1
            current_date += timedelta(days=1)

        # Commit all schedule entries
        await self.db.flush()

    async def _generate_cycle_based_entries(
        self,
        schedule: Schedule,
        workouts: list[Workout],
        training_cycle: list[dict],
        start_date: date,
        duration_weeks: int,
        preferences: dict | None,
    ) -> None:
        """Generate schedule entries based on explicit training cycle from AI agent.

        Uses the training_cycle structure from the workout plan to schedule workouts
        and rest days. The cycle repeats throughout the program duration.

        Args:
            schedule: Schedule to add entries to
            workouts: List of workouts from the plan
            training_cycle: List of cycle items (workout or rest) from plan_snapshot
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
            preferences: User scheduling preferences dict
        """
        # Calculate plan end date
        plan_end_date = start_date + timedelta(weeks=duration_weeks)

        # Get user preferences (handle None values from JSON)
        avoid_dates_raw = preferences.get("avoid_dates") if preferences else None
        avoid_dates = avoid_dates_raw if avoid_dates_raw is not None else []
        preferred_time = self._parse_preferred_time(preferences)

        # Create workout ID lookup
        workout_id_map = {i: workout.id for i, workout in enumerate(workouts)}

        # Start cycling through training cycle
        current_date = start_date
        cycle_idx = 0

        while current_date <= plan_end_date:
            date_str = current_date.isoformat()

            # Skip avoid dates
            if date_str in avoid_dates:
                current_date += timedelta(days=1)
                continue

            # Get current cycle item
            cycle_item = training_cycle[cycle_idx % len(training_cycle)]
            item_type = cycle_item.get("type")

            if item_type == "workout":
                # Schedule workout
                workout_index = cycle_item.get("workout_index")
                if workout_index is not None and workout_index < len(workouts):
                    workout_id = workout_id_map[workout_index]

                    entry = ScheduleEntry(
                        schedule_id=schedule.id,
                        entry_type="workout",
                        entry_date=current_date,
                        entry_time=preferred_time,
                        workout_id=workout_id,
                        meal_id=None,
                        completion_status="scheduled",
                    )
                    self.db.add(entry)

            elif item_type == "rest":
                # Rest day - no workout scheduled (could add rest day entry if needed)
                pass

            # Move to next cycle item and next day
            cycle_idx += 1
            current_date += timedelta(days=1)

        # Commit all schedule entries
        await self.db.flush()

    def _parse_preferred_time(self, preferences: dict | None) -> time | None:
        """Parse preferred workout time from preferences.

        Args:
            preferences: User preferences dict with 'preferred_time' field

        Returns:
            time object or None if no preference
        """
        if not preferences:
            return None

        preferred_time_str = preferences.get("preferred_time", "")
        if not preferred_time_str:
            return None

        # Handle named time slots
        time_mappings = {
            "morning": time(7, 0),
            "afternoon": time(14, 0),
            "evening": time(18, 0),
        }

        if preferred_time_str.lower() in time_mappings:
            return time_mappings[preferred_time_str.lower()]

        # Try to parse specific time like "6:00 AM" or "18:30"
        try:
            # Simple parsing for "HH:MM" or "HH:MM AM/PM"
            time_str = preferred_time_str.strip().upper()
            if "AM" in time_str or "PM" in time_str:
                return datetime.strptime(time_str, "%I:%M %p").time()
            else:
                return datetime.strptime(time_str, "%H:%M").time()
        except (ValueError, AttributeError):
            return None

    def _parse_time_string(self, time_str: str) -> time:
        """Parse time string in various formats to time object.

        Supports formats:
        - 12-hour: '10:00 AM', '2:30 PM', '7:00am'
        - 24-hour: '14:30', '08:00', '19:45'

        Args:
            time_str: Time string to parse

        Returns:
            Parsed time object (defaults to 10:00 if parsing fails)
        """
        try:
            time_str = time_str.strip().upper()
            if "AM" in time_str or "PM" in time_str:
                # Parse 12-hour format (e.g., '10:00 AM', '2:30 PM')
                return datetime.strptime(time_str, "%I:%M %p").time()
            else:
                # Parse 24-hour format (e.g., '14:30', '08:00')
                return datetime.strptime(time_str, "%H:%M").time()
        except (ValueError, AttributeError):
            return time(10, 0)  # Default fallback

    async def _generate_meal_entries(
        self,
        schedule: Schedule,
        meals: list[Meal],
        start_date: date,
        duration_weeks: int,
    ) -> None:
        """Generate schedule entries for meals spanning the entire plan duration.

        Creates daily meal entries for the complete plan duration, including
        any recovery period or post-goal maintenance days.

        Args:
            schedule: Schedule to add entries to
            meals: List of meals from the plan
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
        """
        # Calculate plan end date to ensure complete coverage
        plan_end_date = start_date + timedelta(weeks=duration_weeks)

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

        # Create daily entries for each meal type through entire plan duration
        current_date = start_date
        meal_rotation_index = {meal_type: 0 for meal_type in meals_by_type}

        # Generate entries up to and including the plan end date
        while current_date <= plan_end_date:
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

        # Commit all schedule entries
        await self.db.flush()

    async def _generate_grocery_shopping_entries(
        self,
        schedule: Schedule,
        fitness_plan: FitnessPlan,
        start_date: date,
        duration_weeks: int,
        preferences: dict | None,
    ) -> None:
        """Generate grocery shopping entries from AI-generated explicit schedule.

        Uses the AI-generated grocery_shopping_schedule from the plan's meal_details.
        Supports any frequency pattern: weekly, biweekly, every 15 days, irregular, etc.
        Creates GroceryShoppingTrip entities and links them to schedule entries.

        Args:
            schedule: Schedule to add entries to
            fitness_plan: The fitness plan (contains AI-generated schedule)
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
            preferences: User scheduling preferences dict (mostly unused now)
        """
        from src.models.grocery_trip import GroceryShoppingTrip
        
        # Extract AI-generated schedule from plan_snapshot
        shopping_schedule = []
        grocery_items = []

        if fitness_plan.plan_snapshot and isinstance(fitness_plan.plan_snapshot, dict):
            phases = fitness_plan.plan_snapshot.get("phases", [])
            if phases and len(phases) > 0:
                phase_data = phases[0]
                if isinstance(phase_data, dict):
                    meal_details = phase_data.get("meal_details", {})
                    if isinstance(meal_details, dict):
                        shopping_schedule = meal_details.get("grocery_shopping_schedule", [])
                        grocery_items = meal_details.get("grocery_list", [])

        if not shopping_schedule:
            return  # No schedule generated by AI

        plan_end_date = start_date + timedelta(weeks=duration_weeks)

        # Create a single grocery trip template that will be reused
        grocery_trip = GroceryShoppingTrip(
            name="Weekly Grocery Shopping",
            items={"items": grocery_items},
            estimated_duration_minutes=60,
            notes="Standard weekly grocery shopping trip"
        )
        self.db.add(grocery_trip)
        await self.db.flush()  # Get the ID

        # Process each shopping schedule entry
        for schedule_entry in shopping_schedule:
            day_offset = schedule_entry.get("day_offset", 0)
            time_str = schedule_entry.get("time", "10:00 AM")
            repeats_every = schedule_entry.get("repeats_every")  # Can be None for one-time events
            notes = schedule_entry.get("notes", "")

            # Parse time
            shopping_time = self._parse_time_string(time_str)

            # Calculate first occurrence
            first_date = start_date + timedelta(days=day_offset)

            if repeats_every is None:
                # One-time shopping event
                if first_date <= plan_end_date:
                    entry = ScheduleEntry(
                        schedule_id=schedule.id,
                        entry_type="grocery_shopping",
                        entry_date=first_date,
                        entry_time=shopping_time,
                        grocery_trip_id=grocery_trip.id,
                        user_notes=notes,
                        completion_status="scheduled",
                    )
                    self.db.add(entry)
            else:
                # Repeating shopping event
                current_date = first_date
                while current_date <= plan_end_date:
                    entry = ScheduleEntry(
                        schedule_id=schedule.id,
                        entry_type="grocery_shopping",
                        entry_date=current_date,
                        entry_time=shopping_time,
                        grocery_trip_id=grocery_trip.id,
                        user_notes=notes,
                        completion_status="scheduled",
                    )
                    self.db.add(entry)

                    # Move to next occurrence
                    current_date += timedelta(days=repeats_every)

        await self.db.flush()

    async def _generate_meal_prep_entries(
        self,
        schedule: Schedule,
        fitness_plan: FitnessPlan,
        start_date: date,
        duration_weeks: int,
        preferences: dict | None,
    ) -> None:
        """Generate meal prep entries from AI-generated explicit schedule.

        Uses the AI-generated meal_prep_schedule from the plan's meal_details.
        Supports any frequency pattern: weekly, every 10 days, biweekly, irregular, etc.

        Args:
            schedule: Schedule to add entries to
            fitness_plan: The fitness plan (contains AI-generated schedule)
            start_date: Schedule start date
            duration_weeks: Total plan duration in weeks
            preferences: User scheduling preferences dict (mostly unused now)
        """
        # Extract AI-generated schedule from plan_snapshot
        prep_schedule = []
        prep_sessions = []

        if fitness_plan.plan_snapshot and isinstance(fitness_plan.plan_snapshot, dict):
            phases = fitness_plan.plan_snapshot.get("phases", [])
            if phases and len(phases) > 0:
                phase_data = phases[0]
                if isinstance(phase_data, dict):
                    meal_details = phase_data.get("meal_details", {})
                    if isinstance(meal_details, dict):
                        prep_schedule = meal_details.get("meal_prep_schedule", [])
                        prep_sessions = meal_details.get("meal_prep_sessions", [])

        if not prep_schedule or not prep_sessions:
            return  # No schedule generated by AI

        from src.models.meal_prep import MealPrepSession
        
        plan_end_date = start_date + timedelta(weeks=duration_weeks)

        # Create MealPrepSession entities for each unique session
        session_entities = {}
        for idx, session in enumerate(prep_sessions):
            prep_session = MealPrepSession(
                session_name=session.get("session_name", f"Meal Prep Session {idx + 1}"),
                recipes=session.get("recipes", []),
                duration_minutes=session.get("duration_minutes", 120),
                batch_size=session.get("batch_size", 5),
                instructions=session.get("instructions", []),
                storage_instructions=session.get("storage_instructions", ""),
                notes=session.get("notes", "")
            )
            self.db.add(prep_session)
            session_entities[idx] = prep_session
        
        await self.db.flush()  # Get all IDs

        # Process each prep schedule entry
        for schedule_entry in prep_schedule:
            day_offset = schedule_entry.get("day_offset", 0)
            time_str = schedule_entry.get("time", "14:00")
            session_index = schedule_entry.get("session_index", 0)
            repeats_every = schedule_entry.get("repeats_every")  # Can be None for one-time events
            notes = schedule_entry.get("notes", "")

            # Validate session index
            if session_index not in session_entities:
                continue

            prep_session = session_entities[session_index]
            prep_time = self._parse_time_string(time_str)

            # Calculate first occurrence
            first_date = start_date + timedelta(days=day_offset)

            if repeats_every is None:
                # One-time prep session
                if first_date <= plan_end_date:
                    entry = ScheduleEntry(
                        schedule_id=schedule.id,
                        entry_type="meal_prep",
                        entry_date=first_date,
                        entry_time=prep_time,
                        meal_prep_session_id=prep_session.id,
                        user_notes=notes,
                        completion_status="scheduled",
                    )
                    self.db.add(entry)
            else:
                # Repeating prep session
                current_date = first_date
                while current_date <= plan_end_date:
                    entry = ScheduleEntry(
                        schedule_id=schedule.id,
                        entry_type="meal_prep",
                        entry_date=current_date,
                        entry_time=prep_time,
                        meal_prep_session_id=prep_session.id,
                        user_notes=notes,
                        completion_status="scheduled",
                    )
                    self.db.add(entry)

                    # Move to next occurrence
                    current_date += timedelta(days=repeats_every)

        await self.db.flush()

    async def get_schedule_by_plan(
        self,
        fitness_plan_id: UUID,
    ) -> Schedule | None:
        """Get schedule for a specific fitness plan.

        Args:
            fitness_plan_id: Fitness plan UUID

        Returns:
            Schedule with entries, or None if not found
        """
        stmt = (
            select(Schedule)
            .where(Schedule.fitness_plan_id == fitness_plan_id)
            .options(
                selectinload(Schedule.entries).selectinload(ScheduleEntry.workout),
                selectinload(Schedule.entries).selectinload(ScheduleEntry.meal),
            )
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
                selectinload(ScheduleEntry.grocery_trip),
                selectinload(ScheduleEntry.meal_prep_session),
            )
            .order_by(ScheduleEntry.entry_time, ScheduleEntry.entry_type)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_schedule_range(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[ScheduleEntry]:
        """Get schedule entries for a specific date range.

        Args:
            user_id: User's UUID
            start_date: Start date (inclusive)
            end_date: End date (exclusive)

        Returns:
            List of schedule entries ordered by date and time
        """
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
                selectinload(ScheduleEntry.grocery_trip),
                selectinload(ScheduleEntry.meal_prep_session),
            )
            .order_by(ScheduleEntry.entry_date, ScheduleEntry.entry_time, ScheduleEntry.entry_type)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming_schedule(
        self,
        user_id: UUID,
        days: int = 14,
        start_date: date | None = None,
        include_past_days: int = 7,
    ) -> list[ScheduleEntry]:
        """Get schedule entries for the next N days, optionally including past days.

        Args:
            user_id: User's UUID
            days: Number of days to look ahead (default 14)
            start_date: Optional start date (defaults to today)
            include_past_days: Number of past days to include (default 7)

        Returns:
            List of schedule entries ordered by date and time
        """
        if start_date is None:
            start_date = date.today()

        # Include past days in the query
        actual_start_date = start_date - timedelta(days=include_past_days)
        end_date = start_date + timedelta(days=days)

        stmt = (
            select(ScheduleEntry)
            .join(Schedule)
            .where(
                and_(
                    Schedule.user_id == user_id,
                    ScheduleEntry.entry_date >= actual_start_date,
                    ScheduleEntry.entry_date < end_date,
                )
            )
            .options(
                selectinload(ScheduleEntry.workout),
                selectinload(ScheduleEntry.meal),
                selectinload(ScheduleEntry.grocery_trip),
                selectinload(ScheduleEntry.meal_prep_session),
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
        update_stmt = select(ScheduleEntry).where(
            and_(
                ScheduleEntry.schedule_id == schedule_id,
                ScheduleEntry.completion_status.in_(["scheduled", "rescheduled"]),
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

    async def reschedule_for_disruption(
        self,
        disruption: DisruptionEvent,
    ) -> dict:
        """Intelligently reschedule around a disruption event (FR-016, FR-017, FR-018).

        Implements different strategies based on disruption type and severity:
        - Minor disruptions: Reschedule affected items to available slots
        - Moderate disruptions: Spread items across available days, may extend timeline
        - Severe disruptions: Extend timeline, possibly transition to next phase

        Args:
            disruption: DisruptionEvent with type, dates, severity

        Returns:
            Dictionary with rescheduling details:
            {
                'workouts_affected': int,
                'meals_affected': int,
                'timeline_extension_days': int,
                'rescheduled_workouts': [list of rescheduled workout entries],
                'rescheduled_meals': [list of rescheduled meal entries],
                'new_end_date': date,
                'strategy_applied': str
            }

        Raises:
            ValueError: If disruption's fitness plan or schedule not found
        """
        # Load the schedule for this fitness plan
        schedule_stmt = (
            select(Schedule)
            .where(Schedule.fitness_plan_id == disruption.fitness_plan_id)
            .options(selectinload(Schedule.fitness_plan))
        )
        schedule_result = await self.db.execute(schedule_stmt)
        schedule = schedule_result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found for fitness plan")

        # Load the fitness plan to get end_date
        plan_stmt = select(FitnessPlan).where(FitnessPlan.id == disruption.fitness_plan_id)
        plan_result = await self.db.execute(plan_stmt)
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise ValueError("Fitness plan not found")

        # Calculate disruption duration
        disruption_days = 0
        if disruption.end_date:
            disruption_days = (disruption.end_date - disruption.start_date).days + 1
        else:
            # Estimate based on severity if ongoing
            severity_days_map = {"minor": 3, "moderate": 7, "severe": 14}
            disruption_days = severity_days_map.get(disruption.severity, 7)

        # Find affected schedule entries (scheduled or rescheduled status only)
        affected_entries_stmt = (
            select(ScheduleEntry)
            .where(
                and_(
                    ScheduleEntry.schedule_id == schedule.id,
                    ScheduleEntry.entry_date >= disruption.start_date,
                    ScheduleEntry.entry_date
                    <= (
                        disruption.end_date
                        or disruption.start_date + timedelta(days=disruption_days)
                    ),
                    ScheduleEntry.completion_status.in_(["scheduled", "rescheduled"]),
                )
            )
            .options(
                selectinload(ScheduleEntry.workout),
                selectinload(ScheduleEntry.meal),
            )
        )
        affected_result = await self.db.execute(affected_entries_stmt)
        affected_entries = list(affected_result.scalars().all())

        # Count affected items by type
        affected_workouts = [e for e in affected_entries if e.entry_type == "workout"]
        affected_meals = [e for e in affected_entries if e.entry_type == "meal"]

        # Determine rescheduling strategy based on disruption type and severity
        strategy = self._determine_reschedule_strategy(
            disruption_type=disruption.disruption_type,
            severity=disruption.severity,
            disruption_days=disruption_days,
            workouts_count=len(affected_workouts),
            meals_count=len(affected_meals),
        )

        timeline_extension_days = 0
        rescheduled_workouts = []
        rescheduled_meals = []

        if strategy == "reschedule":
            # Move items to nearest available slots after disruption ends
            resume_date = (
                disruption.end_date or disruption.start_date + timedelta(days=disruption_days)
            ) + timedelta(days=1)

            # Reschedule workouts
            current_workout_date = resume_date
            for entry in affected_workouts:
                entry.entry_date = current_workout_date
                entry.completion_status = "rescheduled"
                rescheduled_workouts.append(
                    {
                        "original_date": str(
                            entry.entry_date
                            - timedelta(days=(current_workout_date - entry.entry_date).days)
                        ),
                        "new_date": str(current_workout_date),
                        "workout_id": str(entry.workout_id),
                    }
                )
                current_workout_date += timedelta(days=2)  # Space out workouts

            # Reschedule meals - spread across available days
            current_meal_date = resume_date
            for entry in affected_meals:
                entry.entry_date = current_meal_date
                entry.completion_status = "rescheduled"
                rescheduled_meals.append(
                    {
                        "original_date": str(
                            entry.entry_date
                            - timedelta(days=(current_meal_date - entry.entry_date).days)
                        ),
                        "new_date": str(current_meal_date),
                        "meal_id": str(entry.meal_id),
                    }
                )
                current_meal_date += timedelta(days=1)

            # Calculate if timeline extension needed
            last_rescheduled_date = max(
                current_workout_date if affected_workouts else resume_date,
                current_meal_date if affected_meals else resume_date,
            )
            if last_rescheduled_date > plan.end_date:
                timeline_extension_days = (last_rescheduled_date - plan.end_date).days
                plan.end_date = last_rescheduled_date

        elif strategy == "skip":
            # Mark affected items as skipped
            for entry in affected_entries:
                entry.completion_status = "skipped"
                entry.skipped_reason = (
                    f"Disruption: {disruption.disruption_type} ({disruption.severity})"
                )
                if entry.entry_type == "workout":
                    rescheduled_workouts.append(
                        {
                            "original_date": str(entry.entry_date),
                            "status": "skipped",
                            "workout_id": str(entry.workout_id),
                        }
                    )
                else:
                    rescheduled_meals.append(
                        {
                            "original_date": str(entry.entry_date),
                            "status": "skipped",
                            "meal_id": str(entry.meal_id),
                        }
                    )

        elif strategy == "extend_timeline":
            # Extend timeline by disruption duration and shift all future entries
            timeline_extension_days = disruption_days
            plan.end_date = plan.end_date + timedelta(days=timeline_extension_days)

            # Shift all entries during and after disruption
            for entry in affected_entries:
                entry.entry_date = entry.entry_date + timedelta(days=timeline_extension_days)
                entry.completion_status = "rescheduled"
                if entry.entry_type == "workout":
                    rescheduled_workouts.append(
                        {
                            "original_date": str(
                                entry.entry_date - timedelta(days=timeline_extension_days)
                            ),
                            "new_date": str(entry.entry_date),
                            "workout_id": str(entry.workout_id),
                        }
                    )
                else:
                    rescheduled_meals.append(
                        {
                            "original_date": str(
                                entry.entry_date - timedelta(days=timeline_extension_days)
                            ),
                            "new_date": str(entry.entry_date),
                            "meal_id": str(entry.meal_id),
                        }
                    )

        # Update schedule metadata
        schedule.last_recalculated_at = datetime.now(UTC)
        schedule.recalculation_reason = (
            f"Disruption: {disruption.disruption_type} ({disruption.severity})"
        )

        await self.db.commit()

        return {
            "workouts_affected": len(affected_workouts),
            "meals_affected": len(affected_meals),
            "timeline_extension_days": timeline_extension_days,
            "rescheduled_workouts": rescheduled_workouts,
            "rescheduled_meals": rescheduled_meals,
            "new_end_date": plan.end_date,
            "strategy_applied": strategy,
        }

    def _determine_reschedule_strategy(
        self,
        disruption_type: str,
        severity: str,
        disruption_days: int,
        workouts_count: int,
        meals_count: int,
    ) -> str:
        """Determine the best rescheduling strategy based on disruption characteristics.

        Args:
            disruption_type: Type of disruption (illness, injury, travel, etc.)
            severity: Severity level (minor, moderate, severe)
            disruption_days: Duration of disruption in days
            workouts_count: Number of workouts affected
            meals_count: Number of meals affected

        Returns:
            Strategy: 'reschedule', 'skip', 'extend_timeline', or 'reassess'
        """
        # Injury-specific logic: severe injuries need careful rescheduling
        if disruption_type == "injury" and severity == "severe":
            return "reassess"  # May need plan modification

        # Travel disruptions: usually can reschedule workouts, keep meal plans
        if disruption_type == "travel":
            if severity == "minor" and disruption_days <= 3:
                return "reschedule"
            return "extend_timeline"

        # Illness severity determines strategy
        if disruption_type == "illness":
            if severity == "minor" and disruption_days <= 2:
                return "reschedule"  # Quick recovery, just move items forward
            elif severity == "moderate" and disruption_days <= 7:
                return "extend_timeline"  # Need time to recover strength
            else:
                return "reassess"  # Severe illness may require plan changes

        # Schedule conflicts: try to reschedule if short duration
        if disruption_type == "schedule_conflict":
            if disruption_days <= 5:
                return "reschedule"
            return "extend_timeline"

        # Default strategy based on severity and duration
        if severity == "minor" and disruption_days <= 3:
            return "reschedule"
        elif severity == "moderate" or disruption_days <= 7:
            return "extend_timeline"
        else:
            return "reassess"
