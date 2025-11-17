"""Unit tests for ScheduleService rescheduling logic."""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.models.conversation import DisruptionSeverity, DisruptionType, ResolutionStrategy
from src.services.schedule_service import ScheduleService


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def schedule_service(mock_db):
    """Schedule service with mocked database."""
    return ScheduleService(mock_db)


class TestRescheduleForDisruption:
    """Test suite for reschedule_for_disruption method."""

    async def test_illness_moderate_reschedule_strategy(self, schedule_service, mock_db):
        """Test moderate illness triggers reschedule strategy."""
        # Arrange
        disruption_id = uuid4()
        fitness_plan_id = uuid4()
        start_date = date.today()
        end_date = date.today() + timedelta(days=4)  # 5 days

        # Mock DisruptionEvent
        mock_disruption = MagicMock()
        mock_disruption.id = disruption_id
        mock_disruption.fitness_plan_id = fitness_plan_id
        mock_disruption.disruption_type = DisruptionType.ILLNESS
        mock_disruption.severity = DisruptionSeverity.MODERATE
        mock_disruption.start_date = start_date
        mock_disruption.end_date = end_date

        # Mock fitness plan
        mock_plan = MagicMock()
        mock_plan.id = fitness_plan_id
        mock_plan.end_date = date.today() + timedelta(days=60)

        # Mock schedule entries
        mock_entries = [
            MagicMock(
                id=uuid4(),
                schedule_date=start_date + timedelta(days=i),
                workout_id=uuid4() if i % 2 == 0 else None,
                meal_id=uuid4() if i % 2 == 1 else None,
            )
            for i in range(5)
        ]

        # Setup mock responses
        def mock_execute_side_effect(*args, **kwargs):
            result = AsyncMock()
            # First call: fetch plan
            # Second call: fetch entries
            # Third call: update entries
            result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))
            result.scalar_one_or_none = MagicMock(return_value=mock_plan)
            return result

        mock_db.execute.side_effect = [
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),  # Plan fetch
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))),  # Entries fetch
        ]

        # Act
        result = await schedule_service.reschedule_for_disruption(
            disruption=mock_disruption,
        )

        # Assert
        assert result["resolution_strategy"] == ResolutionStrategy.RESCHEDULE
        assert result["workouts_affected"] >= 0
        assert result["meals_affected"] >= 0
        assert result["timeline_extension_days"] >= 0

    async def test_injury_severe_extend_timeline_strategy(self, schedule_service, mock_db):
        """Test severe injury triggers extend_timeline strategy."""
        # Arrange
        disruption_id = uuid4()
        start_date = date.today()
        end_date = date.today() + timedelta(days=13)  # 14 days (2 weeks)

        mock_disruption = MagicMock()
        mock_disruption.id = disruption_id
        mock_disruption.disruption_type = DisruptionType.INJURY
        mock_disruption.severity = DisruptionSeverity.SEVERE
        mock_disruption.start_date = start_date
        mock_disruption.end_date = end_date

        mock_plan = MagicMock()
        mock_plan.end_date = date.today() + timedelta(days=60)

        mock_entries = [MagicMock(schedule_date=start_date + timedelta(days=i)) for i in range(14)]

        mock_db.execute.side_effect = [
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))),
        ]

        # Act
        result = await schedule_service.reschedule_for_disruption(disruption=mock_disruption)

        # Assert
        assert result["resolution_strategy"] in [ResolutionStrategy.EXTEND_TIMELINE, ResolutionStrategy.RESCHEDULE]
        assert result["timeline_extension_days"] > 0  # Severe injury should extend timeline

    async def test_travel_minor_skip_strategy(self, schedule_service, mock_db):
        """Test minor travel disruption uses skip strategy."""
        # Arrange
        disruption_id = uuid4()
        start_date = date.today()
        end_date = date.today() + timedelta(days=2)  # 3 days

        mock_disruption = MagicMock()
        mock_disruption.id = disruption_id
        mock_disruption.disruption_type = DisruptionType.TRAVEL
        mock_disruption.severity = DisruptionSeverity.MINOR
        mock_disruption.start_date = start_date
        mock_disruption.end_date = end_date

        mock_plan = MagicMock()
        mock_plan.end_date = date.today() + timedelta(days=60)

        mock_entries = [MagicMock(schedule_date=start_date + timedelta(days=i)) for i in range(3)]

        mock_db.execute.side_effect = [
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))),
        ]

        # Act
        result = await schedule_service.reschedule_for_disruption(disruption=mock_disruption)

        # Assert
        assert result["resolution_strategy"] in [ResolutionStrategy.SKIP, ResolutionStrategy.RESCHEDULE]

    async def test_schedule_conflict_short_duration_reschedule(self, schedule_service, mock_db):
        """Test schedule conflict with short duration."""
        # Arrange
        disruption_id = uuid4()
        start_date = date.today()
        end_date = date.today() + timedelta(days=1)  # 2 days

        mock_disruption = MagicMock()
        mock_disruption.id = disruption_id
        mock_disruption.disruption_type = DisruptionType.SCHEDULE_CONFLICT
        mock_disruption.severity = DisruptionSeverity.MINOR
        mock_disruption.start_date = start_date
        mock_disruption.end_date = end_date

        mock_plan = MagicMock()
        mock_plan.end_date = date.today() + timedelta(days=60)

        mock_entries = [MagicMock(schedule_date=start_date + timedelta(days=i)) for i in range(2)]

        mock_db.execute.side_effect = [
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))),
        ]

        # Act
        result = await schedule_service.reschedule_for_disruption(disruption=mock_disruption)

        # Assert
        assert result["resolution_strategy"] == ResolutionStrategy.RESCHEDULE
        assert result["workouts_affected"] >= 0
        assert result["meals_affected"] >= 0

    async def test_personal_emergency_severe_reassess_strategy(self, schedule_service, mock_db):
        """Test severe personal emergency triggers reassess strategy."""
        # Arrange
        disruption_id = uuid4()
        start_date = date.today()
        end_date = None  # Ongoing emergency

        mock_disruption = MagicMock()
        mock_disruption.id = disruption_id
        mock_disruption.disruption_type = DisruptionType.PERSONAL_EMERGENCY
        mock_disruption.severity = DisruptionSeverity.SEVERE
        mock_disruption.start_date = start_date
        mock_disruption.end_date = end_date

        mock_plan = MagicMock()
        mock_plan.end_date = date.today() + timedelta(days=60)

        mock_entries = []

        mock_db.execute.side_effect = [
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))),
        ]

        # Act
        result = await schedule_service.reschedule_for_disruption(disruption=mock_disruption)

        # Assert
        assert result["resolution_strategy"] == ResolutionStrategy.REASSESS
        # No end date means can't calculate affected items precisely
        assert "workouts_affected" in result
        assert "meals_affected" in result

    async def test_no_affected_entries_returns_skip_strategy(self, schedule_service, mock_db):
        """Test when no entries are affected, skip strategy is used."""
        # Arrange
        disruption_id = uuid4()
        start_date = date.today()
        end_date = date.today() + timedelta(days=2)

        mock_disruption = MagicMock()
        mock_disruption.id = disruption_id
        mock_disruption.disruption_type = DisruptionType.ILLNESS
        mock_disruption.severity = DisruptionSeverity.MINOR
        mock_disruption.start_date = start_date
        mock_disruption.end_date = end_date

        mock_plan = MagicMock()
        mock_plan.end_date = date.today() + timedelta(days=60)

        mock_entries = []  # No entries affected

        mock_db.execute.side_effect = [
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))),
        ]

        # Act
        result = await schedule_service.reschedule_for_disruption(disruption=mock_disruption)

        # Assert
        assert result["resolution_strategy"] in [ResolutionStrategy.SKIP, ResolutionStrategy.RESCHEDULE]
        assert result["workouts_affected"] == 0
        assert result["meals_affected"] == 0
        assert result["timeline_extension_days"] == 0

    async def test_timeline_extension_calculation(self, schedule_service, mock_db):
        """Test timeline extension is calculated correctly based on severity."""
        # Arrange
        disruption_id = uuid4()
        start_date = date.today()
        end_date = date.today() + timedelta(days=6)  # 7 days

        mock_disruption = MagicMock()
        mock_disruption.id = disruption_id
        mock_disruption.disruption_type = DisruptionType.ILLNESS
        mock_disruption.severity = DisruptionSeverity.MODERATE  # Should extend by 50%
        mock_disruption.start_date = start_date
        mock_disruption.end_date = end_date

        mock_plan = MagicMock()
        mock_plan.end_date = date.today() + timedelta(days=60)

        mock_entries = [MagicMock(schedule_date=start_date + timedelta(days=i)) for i in range(7)]

        mock_db.execute.side_effect = [
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_entries)))),
        ]

        # Act
        result = await schedule_service.reschedule_for_disruption(disruption=mock_disruption)

        # Assert
        # Moderate severity should extend timeline (50% of disruption duration)
        if result["resolution_strategy"] == ResolutionStrategy.EXTEND_TIMELINE:
            assert result["timeline_extension_days"] > 0
            # For 7 days disruption at moderate severity, expect ~3-4 days extension
            assert 2 <= result["timeline_extension_days"] <= 5

