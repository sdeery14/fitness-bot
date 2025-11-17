"""Unit tests for date_utils utility module."""
import pytest
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.utils.date_utils import (
    DEFAULT_TIMEZONE,
    get_current_date,
    get_current_datetime,
    parse_date_string,
    format_date,
    add_days,
    days_between,
    weeks_between,
    get_week_start,
    get_week_end,
    get_date_range,
    is_weekend,
    get_next_weekday,
    calculate_schedule_date,
    get_phase_for_date,
    calculate_phase_progress,
    is_consecutive_streak,
    calculate_streak_length,
    combine_datetime,
)


class TestGetCurrentDate:
    """Tests for get_current_date function."""

    def test_get_current_date_utc(self):
        """Test getting current date in UTC."""
        result = get_current_date()
        assert isinstance(result, date)

    def test_get_current_date_with_timezone_string(self):
        """Test getting current date with timezone string."""
        result = get_current_date("America/New_York")
        assert isinstance(result, date)

    def test_get_current_date_with_zoneinfo(self):
        """Test getting current date with ZoneInfo object."""
        tz = ZoneInfo("Europe/London")
        result = get_current_date(tz)
        assert isinstance(result, date)


class TestGetCurrentDatetime:
    """Tests for get_current_datetime function."""

    def test_get_current_datetime_utc(self):
        """Test getting current datetime in UTC."""
        result = get_current_datetime()
        assert isinstance(result, datetime)
        assert result.tzinfo == DEFAULT_TIMEZONE

    def test_get_current_datetime_with_timezone(self):
        """Test getting current datetime with specific timezone."""
        result = get_current_datetime("Asia/Tokyo")
        assert isinstance(result, datetime)
        assert result.tzinfo is not None


class TestParseDateString:
    """Tests for parse_date_string function."""

    def test_parse_valid_date(self):
        """Test parsing valid date strings."""
        result = parse_date_string("2025-11-17")
        assert result == date(2025, 11, 17)

        result = parse_date_string("2000-01-01")
        assert result == date(2000, 1, 1)

    def test_parse_invalid_date_format(self):
        """Test rejection of invalid date formats."""
        with pytest.raises(ValueError):
            parse_date_string("17-11-2025")

        with pytest.raises(ValueError):
            parse_date_string("2025/11/17")

        with pytest.raises(ValueError):
            parse_date_string("not-a-date")


class TestFormatDate:
    """Tests for format_date function."""

    def test_format_date(self):
        """Test formatting date as YYYY-MM-DD."""
        result = format_date(date(2025, 11, 17))
        assert result == "2025-11-17"

        result = format_date(date(2000, 1, 5))
        assert result == "2000-01-05"


class TestAddDays:
    """Tests for add_days function."""

    def test_add_positive_days(self):
        """Test adding positive days."""
        start = date(2025, 11, 17)
        result = add_days(start, 7)
        assert result == date(2025, 11, 24)

    def test_add_negative_days(self):
        """Test subtracting days (negative)."""
        start = date(2025, 11, 17)
        result = add_days(start, -10)
        assert result == date(2025, 11, 7)

    def test_add_zero_days(self):
        """Test adding zero days."""
        start = date(2025, 11, 17)
        result = add_days(start, 0)
        assert result == start


class TestDaysBetween:
    """Tests for days_between function."""

    def test_days_between_future(self):
        """Test calculating days between dates (future)."""
        start = date(2025, 11, 1)
        end = date(2025, 11, 17)
        assert days_between(start, end) == 16

    def test_days_between_past(self):
        """Test calculating days between dates (past)."""
        start = date(2025, 11, 17)
        end = date(2025, 11, 1)
        assert days_between(start, end) == -16

    def test_days_between_same_date(self):
        """Test days between same date."""
        same_date = date(2025, 11, 17)
        assert days_between(same_date, same_date) == 0


class TestWeeksBetween:
    """Tests for weeks_between function."""

    def test_weeks_between(self):
        """Test calculating weeks between dates."""
        start = date(2025, 11, 1)
        end = date(2025, 11, 29)  # 28 days = 4 weeks
        assert weeks_between(start, end) == 4

    def test_weeks_between_partial_week(self):
        """Test that partial weeks are not counted."""
        start = date(2025, 11, 1)
        end = date(2025, 11, 10)  # 9 days = 1 complete week
        assert weeks_between(start, end) == 1


class TestGetWeekStart:
    """Tests for get_week_start function."""

    def test_get_week_start_monday(self):
        """Test getting week start with Monday as first day."""
        # 2025-11-17 is a Sunday
        test_date = date(2025, 11, 17)
        week_start = get_week_start(test_date, week_start_day=0)
        assert week_start.weekday() == 0  # Monday
        assert week_start == date(2025, 11, 17)

    def test_get_week_start_sunday(self):
        """Test getting week start with Sunday as first day."""
        # 2025-11-17 is a Sunday
        test_date = date(2025, 11, 17)
        week_start = get_week_start(test_date, week_start_day=6)
        assert week_start == date(2025, 11, 16)


class TestGetWeekEnd:
    """Tests for get_week_end function."""

    def test_get_week_end(self):
        """Test getting week end date."""
        test_date = date(2025, 11, 17)  # Sunday
        week_end = get_week_end(test_date, week_start_day=0)
        assert week_end == date(2025, 11, 23)  # Next Sunday


class TestGetDateRange:
    """Tests for get_date_range function."""

    def test_get_date_range(self):
        """Test generating list of dates in range."""
        start = date(2025, 11, 1)
        end = date(2025, 11, 5)
        result = get_date_range(start, end)

        assert len(result) == 5
        assert result[0] == date(2025, 11, 1)
        assert result[-1] == date(2025, 11, 5)

    def test_get_date_range_single_day(self):
        """Test date range with same start and end."""
        same_date = date(2025, 11, 17)
        result = get_date_range(same_date, same_date)
        assert len(result) == 1
        assert result[0] == same_date

    def test_get_date_range_reversed(self):
        """Test date range with end before start returns empty."""
        start = date(2025, 11, 5)
        end = date(2025, 11, 1)
        result = get_date_range(start, end)
        assert len(result) == 0


class TestIsWeekend:
    """Tests for is_weekend function."""

    def test_is_weekend_saturday(self):
        """Test Saturday is weekend."""
        saturday = date(2025, 11, 15)  # Saturday
        assert is_weekend(saturday) is True

    def test_is_weekend_sunday(self):
        """Test Sunday is weekend."""
        sunday = date(2025, 11, 16)  # Sunday
        assert is_weekend(sunday) is True

    def test_is_weekend_weekday(self):
        """Test weekdays are not weekend."""
        monday = date(2025, 11, 17)  # Monday
        assert is_weekend(monday) is False

        friday = date(2025, 11, 14)  # Friday
        assert is_weekend(friday) is False


class TestGetNextWeekday:
    """Tests for get_next_weekday function."""

    def test_get_next_weekday(self):
        """Test getting next occurrence of a weekday."""
        # 2025-11-17 is Sunday (weekday 6)
        sunday = date(2025, 11, 16)
        next_monday = get_next_weekday(sunday, 0)  # 0 = Monday
        assert next_monday == date(2025, 11, 17)
        assert next_monday.weekday() == 0

    def test_get_next_weekday_same_day(self):
        """Test getting next occurrence when current day matches."""
        # 2025-11-17 is Monday
        monday = date(2025, 11, 17)
        next_monday = get_next_weekday(monday, 0)  # 0 = Monday
        assert next_monday == date(2025, 11, 24)  # Next Monday, not same day


class TestCalculateScheduleDate:
    """Tests for calculate_schedule_date function."""

    def test_calculate_schedule_date_first_week(self):
        """Test calculating date in first week."""
        start = date(2025, 11, 17)  # Monday
        result = calculate_schedule_date(start, week_number=1, day_of_week=0)  # Monday of week 1
        assert result == date(2025, 11, 17)

    def test_calculate_schedule_date_future_week(self):
        """Test calculating date in future week."""
        start = date(2025, 11, 17)  # Monday
        result = calculate_schedule_date(start, week_number=3, day_of_week=3)  # Thursday of week 3
        expected = date(2025, 12, 4)  # 2 weeks + 3 days from start
        assert result == expected


class TestGetPhaseForDate:
    """Tests for get_phase_for_date function."""

    def test_get_phase_for_date_found(self):
        """Test finding phase for a date within range."""
        phases = [
            {
                "phase_number": 1,
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
            },
            {
                "phase_number": 2,
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
            },
        ]

        result = get_phase_for_date(date(2025, 11, 15), phases)
        assert result is not None
        assert result["phase_number"] == 1

        result = get_phase_for_date(date(2025, 12, 15), phases)
        assert result is not None
        assert result["phase_number"] == 2

    def test_get_phase_for_date_not_found(self):
        """Test when date doesn't fall in any phase."""
        phases = [
            {
                "phase_number": 1,
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
            },
        ]

        result = get_phase_for_date(date(2025, 12, 15), phases)
        assert result is None

    def test_get_phase_for_date_with_date_objects(self):
        """Test with date objects instead of strings."""
        phases = [
            {
                "phase_number": 1,
                "start_date": date(2025, 11, 1),
                "end_date": date(2025, 11, 30),
            },
        ]

        result = get_phase_for_date(date(2025, 11, 15), phases)
        assert result is not None
        assert result["phase_number"] == 1


class TestCalculatePhaseProgress:
    """Tests for calculate_phase_progress function."""

    def test_calculate_phase_progress_start(self):
        """Test phase progress at the beginning."""
        phase_start = date(2025, 11, 1)
        phase_end = date(2025, 11, 30)  # 30 days
        current = date(2025, 11, 1)

        days_completed, days_remaining, progress = calculate_phase_progress(
            current, phase_start, phase_end
        )

        assert days_completed == 1
        assert days_remaining == 29
        assert progress == pytest.approx(3.33, abs=0.1)

    def test_calculate_phase_progress_middle(self):
        """Test phase progress in the middle."""
        phase_start = date(2025, 11, 1)
        phase_end = date(2025, 11, 30)
        current = date(2025, 11, 15)  # Day 15

        days_completed, days_remaining, progress = calculate_phase_progress(
            current, phase_start, phase_end
        )

        assert days_completed == 15
        assert days_remaining == 15
        assert progress == pytest.approx(50.0, abs=0.1)

    def test_calculate_phase_progress_end(self):
        """Test phase progress at the end."""
        phase_start = date(2025, 11, 1)
        phase_end = date(2025, 11, 30)
        current = date(2025, 11, 30)

        days_completed, days_remaining, progress = calculate_phase_progress(
            current, phase_start, phase_end
        )

        assert days_completed == 30
        assert days_remaining == 0
        assert progress == 100.0

    def test_calculate_phase_progress_after_end(self):
        """Test phase progress beyond end date."""
        phase_start = date(2025, 11, 1)
        phase_end = date(2025, 11, 30)
        current = date(2025, 12, 5)

        days_completed, days_remaining, progress = calculate_phase_progress(
            current, phase_start, phase_end
        )

        assert days_remaining == 0  # Can't be negative
        assert progress == 100.0  # Capped at 100%


class TestIsConsecutiveStreak:
    """Tests for is_consecutive_streak function."""

    def test_is_consecutive_streak_true(self):
        """Test consecutive dates return True."""
        dates = [
            date(2025, 11, 15),
            date(2025, 11, 16),
            date(2025, 11, 17),
        ]
        assert is_consecutive_streak(dates) is True

    def test_is_consecutive_streak_false(self):
        """Test non-consecutive dates return False."""
        dates = [
            date(2025, 11, 15),
            date(2025, 11, 17),  # Gap: missing 11-16
            date(2025, 11, 18),
        ]
        assert is_consecutive_streak(dates) is False

    def test_is_consecutive_streak_single_date(self):
        """Test single date is considered consecutive."""
        dates = [date(2025, 11, 17)]
        assert is_consecutive_streak(dates) is True

    def test_is_consecutive_streak_empty(self):
        """Test empty list is considered consecutive."""
        assert is_consecutive_streak([]) is True

    def test_is_consecutive_streak_unsorted(self):
        """Test that unsorted consecutive dates still work."""
        dates = [
            date(2025, 11, 17),
            date(2025, 11, 15),
            date(2025, 11, 16),
        ]
        assert is_consecutive_streak(dates) is True


class TestCalculateStreakLength:
    """Tests for calculate_streak_length function."""

    def test_calculate_streak_length_current(self):
        """Test calculating current streak."""
        reference = date(2025, 11, 17)
        dates = [
            date(2025, 11, 15),
            date(2025, 11, 16),
            date(2025, 11, 17),
        ]
        streak = calculate_streak_length(dates, reference)
        assert streak == 3

    def test_calculate_streak_length_broken(self):
        """Test streak calculation with gap."""
        reference = date(2025, 11, 17)
        dates = [
            date(2025, 11, 10),
            date(2025, 11, 11),
            date(2025, 11, 13),  # Gap on 11-12
            date(2025, 11, 16),
            date(2025, 11, 17),
        ]
        streak = calculate_streak_length(dates, reference)
        assert streak == 2  # Only 11-16 and 11-17

    def test_calculate_streak_length_no_recent_activity(self):
        """Test streak is 0 when no recent activity."""
        reference = date(2025, 11, 17)
        dates = [
            date(2025, 11, 10),
            date(2025, 11, 11),
        ]
        streak = calculate_streak_length(dates, reference)
        assert streak == 0

    def test_calculate_streak_length_empty(self):
        """Test empty dates returns 0 streak."""
        streak = calculate_streak_length([], date(2025, 11, 17))
        assert streak == 0


class TestCombineDatetime:
    """Tests for combine_datetime function."""

    def test_combine_datetime_utc(self):
        """Test combining date and time with UTC timezone."""
        date_obj = date(2025, 11, 17)
        time_obj = time(14, 30, 0)
        result = combine_datetime(date_obj, time_obj)

        assert result.date() == date_obj
        assert result.time() == time_obj
        assert result.tzinfo == DEFAULT_TIMEZONE

    def test_combine_datetime_with_timezone_string(self):
        """Test combining with timezone string."""
        date_obj = date(2025, 11, 17)
        time_obj = time(14, 30, 0)
        result = combine_datetime(date_obj, time_obj, "America/New_York")

        assert result.date() == date_obj
        assert result.time() == time_obj
        assert result.tzinfo == ZoneInfo("America/New_York")

    def test_combine_datetime_with_zoneinfo(self):
        """Test combining with ZoneInfo object."""
        date_obj = date(2025, 11, 17)
        time_obj = time(14, 30, 0)
        tz = ZoneInfo("Europe/London")
        result = combine_datetime(date_obj, time_obj, tz)

        assert result.date() == date_obj
        assert result.time() == time_obj
        assert result.tzinfo == tz
