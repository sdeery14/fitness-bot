"""Date and time utilities for timezone handling and schedule calculations."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Any


# Default timezone (UTC)
DEFAULT_TIMEZONE = ZoneInfo("UTC")


def get_current_date(timezone: str | ZoneInfo = DEFAULT_TIMEZONE) -> date:
    """Get current date in specified timezone.

    Args:
        timezone: Timezone string (e.g., 'America/New_York') or ZoneInfo object

    Returns:
        Current date in specified timezone
    """
    if isinstance(timezone, str):
        timezone = ZoneInfo(timezone)

    return datetime.now(timezone).date()


def get_current_datetime(timezone: str | ZoneInfo = DEFAULT_TIMEZONE) -> datetime:
    """Get current datetime in specified timezone.

    Args:
        timezone: Timezone string or ZoneInfo object

    Returns:
        Current datetime in specified timezone
    """
    if isinstance(timezone, str):
        timezone = ZoneInfo(timezone)

    return datetime.now(timezone)


def parse_date_string(date_string: str) -> date:
    """Parse date string in YYYY-MM-DD format.

    Args:
        date_string: Date string

    Returns:
        Date object

    Raises:
        ValueError: If date format is invalid
    """
    return datetime.strptime(date_string, "%Y-%m-%d").date()


def format_date(date_obj: date) -> str:
    """Format date as YYYY-MM-DD string.

    Args:
        date_obj: Date object

    Returns:
        Formatted date string
    """
    return date_obj.strftime("%Y-%m-%d")


def add_days(date_obj: date, days: int) -> date:
    """Add days to a date.

    Args:
        date_obj: Date object
        days: Number of days to add (can be negative)

    Returns:
        New date
    """
    return date_obj + timedelta(days=days)


def days_between(start_date: date, end_date: date) -> int:
    """Calculate number of days between two dates.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Number of days (positive if end_date > start_date)
    """
    return (end_date - start_date).days


def weeks_between(start_date: date, end_date: date) -> int:
    """Calculate number of weeks between two dates.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Number of complete weeks
    """
    return days_between(start_date, end_date) // 7


def get_week_start(date_obj: date, week_start_day: int = 0) -> date:
    """Get the start of the week for a given date.

    Args:
        date_obj: Date object
        week_start_day: Day of week for week start (0=Monday, 6=Sunday)

    Returns:
        Date of the week start
    """
    days_since_week_start = (date_obj.weekday() - week_start_day) % 7
    return date_obj - timedelta(days=days_since_week_start)


def get_week_end(date_obj: date, week_start_day: int = 0) -> date:
    """Get the end of the week for a given date.

    Args:
        date_obj: Date object
        week_start_day: Day of week for week start (0=Monday, 6=Sunday)

    Returns:
        Date of the week end
    """
    week_start = get_week_start(date_obj, week_start_day)
    return week_start + timedelta(days=6)


def get_date_range(start_date: date, end_date: date) -> list[date]:
    """Generate a list of dates in a range (inclusive).

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of dates from start to end (inclusive)
    """
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    return dates


def is_weekend(date_obj: date) -> bool:
    """Check if a date falls on a weekend.

    Args:
        date_obj: Date object

    Returns:
        True if Saturday or Sunday
    """
    return date_obj.weekday() >= 5  # 5=Saturday, 6=Sunday


def get_next_weekday(date_obj: date, target_weekday: int) -> date:
    """Get the next occurrence of a specific weekday.

    Args:
        date_obj: Starting date
        target_weekday: Target day of week (0=Monday, 6=Sunday)

    Returns:
        Next date with the specified weekday
    """
    days_ahead = (target_weekday - date_obj.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return date_obj + timedelta(days=days_ahead)


def calculate_schedule_date(
    start_date: date,
    week_number: int,
    day_of_week: int,
) -> date:
    """Calculate a specific schedule date based on week and day.

    Args:
        start_date: Plan start date
        week_number: Week number (1-indexed)
        day_of_week: Day of week (0=Monday, 6=Sunday)

    Returns:
        Calculated date
    """
    # Calculate the start of the target week
    week_start = start_date + timedelta(weeks=week_number - 1)

    # Adjust to the correct day of the week
    days_offset = (day_of_week - week_start.weekday()) % 7
    return week_start + timedelta(days=days_offset)


def get_phase_for_date(
    current_date: date,
    phases: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Determine which phase a date falls into.

    Args:
        current_date: Date to check
        phases: List of phase dictionaries with start_date and end_date

    Returns:
        Phase dict or None if no matching phase
    """
    for phase in phases:
        start_date = parse_date_string(phase["start_date"]) if isinstance(phase["start_date"], str) else phase["start_date"]
        end_date = parse_date_string(phase["end_date"]) if isinstance(phase["end_date"], str) else phase["end_date"]

        if start_date <= current_date <= end_date:
            return phase

    return None


def calculate_phase_progress(
    current_date: date,
    phase_start: date,
    phase_end: date,
) -> tuple[int, int, float]:
    """Calculate progress through a phase.

    Args:
        current_date: Current date
        phase_start: Phase start date
        phase_end: Phase end date

    Returns:
        Tuple of (days_completed, days_remaining, progress_percentage)
    """
    total_days = days_between(phase_start, phase_end) + 1  # Inclusive
    days_completed = days_between(phase_start, current_date) + 1
    days_remaining = max(0, days_between(current_date, phase_end))

    progress_percentage = min(100.0, (days_completed / total_days) * 100 if total_days > 0 else 0.0)

    return days_completed, days_remaining, progress_percentage


def is_consecutive_streak(dates: list[date]) -> bool:
    """Check if a list of dates represents a consecutive streak.

    Args:
        dates: List of dates (should be sorted)

    Returns:
        True if dates are consecutive
    """
    if len(dates) <= 1:
        return True

    sorted_dates = sorted(dates)

    for i in range(1, len(sorted_dates)):
        if days_between(sorted_dates[i - 1], sorted_dates[i]) != 1:
            return False

    return True


def calculate_streak_length(dates: list[date], reference_date: date | None = None) -> int:
    """Calculate the current streak length ending at reference_date.

    Args:
        dates: List of activity dates
        reference_date: Reference date (defaults to today)

    Returns:
        Length of current consecutive streak
    """
    if not dates:
        return 0

    if reference_date is None:
        reference_date = get_current_date()

    sorted_dates = sorted(dates, reverse=True)

    streak = 0
    expected_date = reference_date

    for activity_date in sorted_dates:
        if activity_date == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        elif activity_date < expected_date:
            # Gap in streak
            break

    return streak


def combine_datetime(date_obj: date, time_obj: time, timezone: str | ZoneInfo = DEFAULT_TIMEZONE) -> datetime:
    """Combine date and time into a datetime with timezone.

    Args:
        date_obj: Date object
        time_obj: Time object
        timezone: Timezone string or ZoneInfo object

    Returns:
        Combined datetime with timezone
    """
    if isinstance(timezone, str):
        timezone = ZoneInfo(timezone)

    return datetime.combine(date_obj, time_obj, tzinfo=timezone)
