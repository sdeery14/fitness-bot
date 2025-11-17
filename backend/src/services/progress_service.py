"""Progress service for tracking adherence, measurements, and milestones."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.progress import ProgressRecord
from src.models.schedule import Schedule, ScheduleEntry


class ProgressService:
    """Service for progress tracking and analytics."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize progress service.

        Args:
            db: Database session for progress queries
        """
        self.db = db

    async def calculate_adherence(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Decimal]:
        """Calculate adherence rates for a date range.

        Args:
            user_id: User's UUID
            start_date: Start date for calculation (defaults to 7 days ago)
            end_date: End date for calculation (defaults to today)

        Returns:
            Dictionary with adherence metrics:
            - workout_adherence: Percentage of workouts completed
            - meal_adherence: Percentage of meals completed
            - overall_adherence: Combined adherence rate
            - total_scheduled: Total activities scheduled
            - total_completed: Total activities completed
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=7)
        if end_date is None:
            end_date = date.today()

        # Query schedule entries for the date range
        stmt = (
            select(
                ScheduleEntry.entry_type,
                ScheduleEntry.completion_status,
                func.count(ScheduleEntry.id).label("count"),
            )
            .join(Schedule)
            .where(
                and_(
                    Schedule.user_id == user_id,
                    ScheduleEntry.entry_date >= start_date,
                    ScheduleEntry.entry_date <= end_date,
                )
            )
            .group_by(ScheduleEntry.entry_type, ScheduleEntry.completion_status)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        # Calculate adherence by type
        workouts_scheduled = 0
        workouts_completed = 0
        meals_scheduled = 0
        meals_completed = 0

        for row in rows:
            entry_type, status, count = row
            if entry_type == "workout":
                if status in ["scheduled", "completed", "skipped"]:
                    workouts_scheduled += count
                if status == "completed":
                    workouts_completed += count
            elif entry_type == "meal":
                if status in ["scheduled", "completed", "skipped"]:
                    meals_scheduled += count
                if status == "completed":
                    meals_completed += count

        # Calculate percentages
        workout_adherence = (
            Decimal(workouts_completed) / Decimal(workouts_scheduled) * 100
            if workouts_scheduled > 0
            else Decimal(0)
        )
        meal_adherence = (
            Decimal(meals_completed) / Decimal(meals_scheduled) * 100
            if meals_scheduled > 0
            else Decimal(0)
        )

        total_scheduled = workouts_scheduled + meals_scheduled
        total_completed = workouts_completed + meals_completed
        overall_adherence = (
            Decimal(total_completed) / Decimal(total_scheduled) * 100
            if total_scheduled > 0
            else Decimal(0)
        )

        return {
            "workout_adherence": workout_adherence.quantize(Decimal("0.01")),
            "meal_adherence": meal_adherence.quantize(Decimal("0.01")),
            "overall_adherence": overall_adherence.quantize(Decimal("0.01")),
            "total_scheduled": total_scheduled,
            "total_completed": total_completed,
            "workouts_scheduled": workouts_scheduled,
            "workouts_completed": workouts_completed,
            "meals_scheduled": meals_scheduled,
            "meals_completed": meals_completed,
        }

    async def get_progress_summary(
        self,
        user_id: UUID,
        fitness_plan_id: UUID | None = None,
    ) -> dict:
        """Get comprehensive progress summary for a user.

        Args:
            user_id: User's UUID
            fitness_plan_id: Optional fitness plan to filter by

        Returns:
            Dictionary with progress summary including:
            - current_streak: Current streak of consecutive active days
            - weekly_adherence: Adherence rate for the last 7 days
            - monthly_adherence: Adherence rate for the last 30 days
            - total_workouts_completed: Total workouts ever completed
            - total_measurements: Count of body measurements logged
            - recent_milestones: List of recent milestone achievements
            - latest_measurements: Most recent body measurements
        """
        # Calculate adherence rates
        weekly = await self.calculate_adherence(
            user_id=user_id,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
        )

        monthly = await self.calculate_adherence(
            user_id=user_id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        # Get current streak
        streak = await self.get_streak(user_id)

        # Get recent milestones
        milestones_stmt = (
            select(ProgressRecord)
            .where(
                and_(
                    ProgressRecord.user_id == user_id,
                    ProgressRecord.milestone_achieved.is_(True),
                )
            )
            .order_by(desc(ProgressRecord.record_date))
            .limit(5)
        )
        milestones_result = await self.db.execute(milestones_stmt)
        milestones = list(milestones_result.scalars().all())

        # Get latest measurements
        measurements_stmt = (
            select(ProgressRecord)
            .where(
                and_(
                    ProgressRecord.user_id == user_id,
                    ProgressRecord.record_type == "measurement",
                )
            )
            .order_by(desc(ProgressRecord.record_date))
            .limit(1)
        )
        measurements_result = await self.db.execute(measurements_stmt)
        latest_measurement = measurements_result.scalar_one_or_none()

        # Count total workouts (from progress records)
        total_workouts_stmt = select(func.sum(ProgressRecord.workouts_completed_today)).where(
            ProgressRecord.user_id == user_id
        )
        total_workouts_result = await self.db.execute(total_workouts_stmt)
        total_workouts = total_workouts_result.scalar() or 0

        return {
            "current_streak_days": streak,
            "weekly_adherence": weekly,
            "monthly_adherence": monthly,
            "total_workouts_completed": int(total_workouts),
            "recent_milestones": [
                {
                    "date": m.record_date,
                    "description": m.milestone_description,
                }
                for m in milestones
            ],
            "latest_measurements": {
                "date": latest_measurement.record_date if latest_measurement else None,
                "weight_lbs": float(latest_measurement.weight_lbs) if latest_measurement and latest_measurement.weight_lbs else None,
                "body_fat_percentage": float(latest_measurement.body_fat_percentage) if latest_measurement and latest_measurement.body_fat_percentage else None,
                "measurements": latest_measurement.measurements if latest_measurement else None,
            } if latest_measurement else None,
        }

    async def record_daily_summary(
        self,
        user_id: UUID,
        fitness_plan_id: UUID | None,
        record_date: date,
        workouts_completed: int = 0,
        meals_completed: int = 0,
        energy_level: int | None = None,
        mood: str | None = None,
        user_notes: str | None = None,
    ) -> ProgressRecord:
        """Record a daily progress summary.

        Typically called automatically at end of day or when user reviews their day.

        Args:
            user_id: User's UUID
            fitness_plan_id: Optional fitness plan ID
            record_date: Date of the summary
            workouts_completed: Number of workouts completed
            meals_completed: Number of meals completed
            energy_level: Energy level (1-10)
            mood: Mood description
            user_notes: User notes for the day

        Returns:
            Created progress record
        """
        # Calculate adherence for the week leading up to this date
        weekly_adherence_data = await self.calculate_adherence(
            user_id=user_id,
            start_date=record_date - timedelta(days=7),
            end_date=record_date,
        )

        # Get total workouts completed so far
        total_stmt = select(func.sum(ProgressRecord.workouts_completed_today)).where(
            and_(
                ProgressRecord.user_id == user_id,
                ProgressRecord.record_date < record_date,
            )
        )
        total_result = await self.db.execute(total_stmt)
        total_workouts = total_result.scalar() or 0

        # Calculate current streak
        streak = await self.get_streak(user_id, as_of_date=record_date)

        # Create progress record
        record = ProgressRecord(
            user_id=user_id,
            fitness_plan_id=fitness_plan_id,
            record_date=record_date,
            record_type="daily_summary",
            workouts_completed_today=workouts_completed,
            meals_completed_today=meals_completed,
            weekly_adherence_rate=weekly_adherence_data["overall_adherence"],
            total_workouts_completed=int(total_workouts) + workouts_completed,
            current_streak_days=streak,
            energy_level=energy_level,
            mood=mood,
            user_notes=user_notes,
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        return record

    async def get_streak(
        self,
        user_id: UUID,
        as_of_date: date | None = None,
    ) -> int:
        """Calculate the user's current streak of consecutive active days.

        An "active day" is a day where the user completed at least one workout or meal.

        Args:
            user_id: User's UUID
            as_of_date: Date to calculate streak up to (defaults to today)

        Returns:
            Number of consecutive days with activity
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all schedule entries ordered by date (descending)
        stmt = (
            select(ScheduleEntry.entry_date, ScheduleEntry.completion_status)
            .join(Schedule)
            .where(
                and_(
                    Schedule.user_id == user_id,
                    ScheduleEntry.entry_date <= as_of_date,
                    ScheduleEntry.completion_status == "completed",
                )
            )
            .order_by(desc(ScheduleEntry.entry_date))
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return 0

        # Group completions by date
        completed_dates = set()
        for row in rows:
            completed_dates.add(row[0])

        # Count consecutive days backwards from as_of_date
        streak = 0
        current_date = as_of_date

        while current_date in completed_dates:
            streak += 1
            current_date -= timedelta(days=1)

        return streak

    async def log_measurement(
        self,
        user_id: UUID,
        fitness_plan_id: UUID | None,
        weight_lbs: Decimal | None = None,
        body_fat_percentage: Decimal | None = None,
        measurements: dict[str, float] | None = None,
        energy_level: int | None = None,
        mood: str | None = None,
        user_notes: str | None = None,
    ) -> ProgressRecord:
        """Log body measurements.

        Args:
            user_id: User's UUID
            fitness_plan_id: Optional fitness plan ID
            weight_lbs: Weight in pounds
            body_fat_percentage: Body fat percentage
            measurements: Body measurements dict (chest, waist, hips, etc.)
            energy_level: Energy level (1-10)
            mood: Mood description
            user_notes: User notes

        Returns:
            Created progress record
        """
        record = ProgressRecord(
            user_id=user_id,
            fitness_plan_id=fitness_plan_id,
            record_date=date.today(),
            record_type="measurement",
            weight_lbs=weight_lbs,
            body_fat_percentage=body_fat_percentage,
            measurements=measurements,
            energy_level=energy_level,
            mood=mood,
            user_notes=user_notes,
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        return record

    async def detect_milestones(
        self,
        user_id: UUID,
        fitness_plan_id: UUID,
    ) -> list[dict]:
        """Detect milestone achievements for a user's fitness plan.

        Analyzes progress data to identify if user has reached any milestones:
        - Streak milestones (7, 14, 30, 60, 90, 180 days)
        - Total workout milestones (10, 25, 50, 100, 250, 500 workouts)
        - Weight loss milestones (5 lbs, 10 lbs, 20 lbs, 50 lbs)
        - Adherence milestones (30 days of 80%+ adherence)
        - Phase completion milestones

        Args:
            user_id: User's UUID
            fitness_plan_id: Fitness plan's UUID

        Returns:
            List of newly detected milestones with details
        """
        milestones_detected = []

        # Check streak milestones
        current_streak = await self.get_streak(user_id)
        streak_thresholds = [7, 14, 30, 60, 90, 180, 365]

        for threshold in streak_thresholds:
            if current_streak >= threshold:
                # Check if this milestone was already recorded
                existing_stmt = (
                    select(ProgressRecord)
                    .where(
                        and_(
                            ProgressRecord.user_id == user_id,
                            ProgressRecord.fitness_plan_id == fitness_plan_id,
                            ProgressRecord.milestone_achieved.is_(True),
                            ProgressRecord.milestone_description.like(f"%{threshold} day streak%"),
                        )
                    )
                    .limit(1)
                )
                existing_result = await self.db.execute(existing_stmt)
                existing = existing_result.scalar_one_or_none()

                if not existing:
                    milestones_detected.append({
                        "type": "streak",
                        "value": threshold,
                        "description": f"Achieved {threshold} day streak!",
                        "title": f"{threshold} Day Streak 🔥",
                        "message": f"You've been consistent for {threshold} consecutive days. Keep it up!",
                    })

        # Check total workout milestones
        total_workouts_stmt = select(func.sum(ProgressRecord.workouts_completed_today)).where(
            and_(
                ProgressRecord.user_id == user_id,
                ProgressRecord.fitness_plan_id == fitness_plan_id,
            )
        )
        total_workouts_result = await self.db.execute(total_workouts_stmt)
        total_workouts = total_workouts_result.scalar() or 0

        workout_thresholds = [10, 25, 50, 100, 250, 500, 1000]
        for threshold in workout_thresholds:
            if total_workouts >= threshold:
                # Check if milestone already recorded
                existing_stmt = (
                    select(ProgressRecord)
                    .where(
                        and_(
                            ProgressRecord.user_id == user_id,
                            ProgressRecord.fitness_plan_id == fitness_plan_id,
                            ProgressRecord.milestone_achieved.is_(True),
                            ProgressRecord.milestone_description.like(f"%{threshold} workouts%"),
                        )
                    )
                    .limit(1)
                )
                existing_result = await self.db.execute(existing_stmt)
                existing = existing_result.scalar_one_or_none()

                if not existing:
                    milestones_detected.append({
                        "type": "total_workouts",
                        "value": threshold,
                        "description": f"Completed {threshold} workouts!",
                        "title": f"{threshold} Workouts Complete 💪",
                        "message": f"You've crushed {threshold} workouts. Your dedication is paying off!",
                    })

        # Check weight loss milestones (if applicable)
        # Get first and latest measurements
        first_measurement_stmt = (
            select(ProgressRecord)
            .where(
                and_(
                    ProgressRecord.user_id == user_id,
                    ProgressRecord.fitness_plan_id == fitness_plan_id,
                    ProgressRecord.weight_lbs.isnot(None),
                )
            )
            .order_by(ProgressRecord.record_date.asc())
            .limit(1)
        )
        first_result = await self.db.execute(first_measurement_stmt)
        first_measurement = first_result.scalar_one_or_none()

        latest_measurement_stmt = (
            select(ProgressRecord)
            .where(
                and_(
                    ProgressRecord.user_id == user_id,
                    ProgressRecord.fitness_plan_id == fitness_plan_id,
                    ProgressRecord.weight_lbs.isnot(None),
                )
            )
            .order_by(ProgressRecord.record_date.desc())
            .limit(1)
        )
        latest_result = await self.db.execute(latest_measurement_stmt)
        latest_measurement = latest_result.scalar_one_or_none()

        if first_measurement and latest_measurement and first_measurement.weight_lbs and latest_measurement.weight_lbs:
            weight_lost = float(first_measurement.weight_lbs - latest_measurement.weight_lbs)

            if weight_lost > 0:  # Only for weight loss goals
                weight_thresholds = [5, 10, 20, 30, 50, 75, 100]
                for threshold in weight_thresholds:
                    if weight_lost >= threshold:
                        existing_stmt = (
                            select(ProgressRecord)
                            .where(
                                and_(
                                    ProgressRecord.user_id == user_id,
                                    ProgressRecord.fitness_plan_id == fitness_plan_id,
                                    ProgressRecord.milestone_achieved.is_(True),
                                    ProgressRecord.milestone_description.like(f"%{threshold} lbs lost%"),
                                )
                            )
                            .limit(1)
                        )
                        existing_result = await self.db.execute(existing_stmt)
                        existing = existing_result.scalar_one_or_none()

                        if not existing:
                            milestones_detected.append({
                                "type": "weight_loss",
                                "value": threshold,
                                "description": f"Lost {threshold} lbs!",
                                "title": f"{threshold} lbs Lost 🎉",
                                "message": f"You've lost {threshold} pounds! Your hard work is showing results!",
                            })

        # Check adherence consistency milestone (30 days of 80%+ adherence)
        thirty_days_adherence = await self.calculate_adherence(
            user_id=user_id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        if thirty_days_adherence["overall_adherence"] >= 80:
            existing_stmt = (
                select(ProgressRecord)
                .where(
                    and_(
                        ProgressRecord.user_id == user_id,
                        ProgressRecord.fitness_plan_id == fitness_plan_id,
                        ProgressRecord.milestone_achieved.is_(True),
                        ProgressRecord.milestone_description.like("%30 days of high adherence%"),
                    )
                )
                .order_by(ProgressRecord.record_date.desc())
                .limit(1)
            )
            existing_result = await self.db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()

            # Only record if not achieved in last 30 days
            if not existing or (existing.record_date < date.today() - timedelta(days=30)):
                milestones_detected.append({
                    "type": "adherence_consistency",
                    "value": 30,
                    "description": "30 days of 80%+ adherence!",
                    "title": "Consistency Champion 🏆",
                    "message": f"You've maintained {thirty_days_adherence['overall_adherence']:.0f}% adherence for 30 days!",
                })

        return milestones_detected

    async def record_milestone_achievement(
        self,
        user_id: UUID,
        fitness_plan_id: UUID,
        milestone: dict,
    ) -> ProgressRecord:
        """Record a milestone achievement in the progress history.

        Args:
            user_id: User's UUID
            fitness_plan_id: Fitness plan's UUID
            milestone: Milestone details from detect_milestones

        Returns:
            Created progress record for the milestone
        """
        record = ProgressRecord(
            user_id=user_id,
            fitness_plan_id=fitness_plan_id,
            record_date=date.today(),
            record_type="milestone",
            milestone_achieved=True,
            milestone_description=milestone["description"],
            user_notes=milestone.get("message", ""),
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        return record

