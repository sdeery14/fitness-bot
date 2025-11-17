"""Unit tests for progress service milestone detection."""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.progress_service import ProgressService


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def progress_service(mock_db_session):
    """Create a progress service instance with mocked session."""
    return ProgressService(mock_db_session)


@pytest.mark.asyncio
async def test_detect_streak_milestone_7_days(progress_service, mock_db_session):
    """Test detecting 7-day streak milestone."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Mock 7 consecutive days of workouts
    today = date.today()
    workout_dates = [today - timedelta(days=i) for i in range(7)]

    # Mock database query to return 7 consecutive records
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = workout_dates
    mock_db_session.execute.side_effect = [
        mock_result,  # Workout dates query
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Existing milestone check
    ]

    # Call detect_milestones
    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # Verify 7-day streak milestone was detected
    assert len(milestones) == 1
    assert milestones[0]["type"] == "streak"
    assert "7 days" in milestones[0]["description"]


@pytest.mark.asyncio
async def test_detect_streak_milestone_30_days(progress_service, mock_db_session):
    """Test detecting 30-day streak milestone."""
    # Mock 30 consecutive days
    today = date.today()
    workout_dates = [today - timedelta(days=i) for i in range(30)]
    user_id = uuid4()
    fitness_plan_id = uuid4()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = workout_dates
    mock_db_session.execute.side_effect = [
        mock_result,  # Workout dates
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Existing check
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # Should detect 30-day milestone (and possibly 7, 14 if logic detects all)
    streak_milestones = [m for m in milestones if m["type"] == "streak"]
    assert len(streak_milestones) >= 1
    assert any("30 days" in m["description"] for m in streak_milestones)


@pytest.mark.asyncio
async def test_detect_workout_milestone_10_workouts(progress_service, mock_db_session):
    """Test detecting 10 completed workouts milestone."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Mock 10 total workouts
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 10

    mock_db_session.execute.side_effect = [
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Workout dates (empty for this test)
        mock_count_result,  # Workout count query
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Existing milestone check
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # Verify 10 workouts milestone
    workout_milestones = [m for m in milestones if m["type"] == "workouts"]
    assert len(workout_milestones) >= 1
    assert any("10" in m["description"] for m in workout_milestones)


@pytest.mark.asyncio
async def test_detect_workout_milestone_100_workouts(progress_service, mock_db_session):
    """Test detecting 100 completed workouts milestone."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 100

    mock_db_session.execute.side_effect = [
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        mock_count_result,
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    workout_milestones = [m for m in milestones if m["type"] == "workouts"]
    assert len(workout_milestones) >= 1
    assert any("100" in m["description"] for m in workout_milestones)


@pytest.mark.asyncio
async def test_detect_weight_loss_milestone_5_lbs(progress_service, mock_db_session):
    """Test detecting 5 lbs weight loss milestone."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Mock weight progress: started at 200 lbs, now at 195 lbs
    mock_initial_weight = MagicMock()
    mock_initial_weight.scalar.return_value = 200.0

    mock_latest_weight = MagicMock()
    mock_latest_weight.scalar.return_value = 195.0

    mock_db_session.execute.side_effect = [
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Workout dates
        MagicMock(scalar=MagicMock(return_value=0)),  # Workout count
        mock_initial_weight,  # Initial weight
        mock_latest_weight,  # Latest weight
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Existing milestone
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # Verify weight loss milestone
    weight_milestones = [m for m in milestones if m["type"] == "weight_loss"]
    assert len(weight_milestones) >= 1
    assert any("5" in m["description"] for m in weight_milestones)


@pytest.mark.asyncio
async def test_detect_weight_loss_milestone_20_lbs(progress_service, mock_db_session):
    """Test detecting 20 lbs weight loss milestone."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Started at 220 lbs, now at 200 lbs
    mock_initial_weight = MagicMock()
    mock_initial_weight.scalar.return_value = 220.0

    mock_latest_weight = MagicMock()
    mock_latest_weight.scalar.return_value = 200.0

    mock_db_session.execute.side_effect = [
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        MagicMock(scalar=MagicMock(return_value=0)),
        mock_initial_weight,
        mock_latest_weight,
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    weight_milestones = [m for m in milestones if m["type"] == "weight_loss"]
    assert len(weight_milestones) >= 1
    assert any("20" in m["description"] for m in weight_milestones)


@pytest.mark.asyncio
async def test_detect_adherence_milestone_30_days_80_percent(progress_service, mock_db_session):
    """Test detecting 30 days of 80%+ adherence milestone."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Mock 30 days with 80% adherence (24 out of 30 workouts)
    today = date.today()
    workout_dates = [today - timedelta(days=i) for i in range(24)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = workout_dates

    mock_db_session.execute.side_effect = [
        mock_result,  # Workout dates - 24 days in last 30
        MagicMock(scalar=MagicMock(return_value=24)),  # Workout count
        MagicMock(scalar=MagicMock(return_value=None)),  # Initial weight
        MagicMock(scalar=MagicMock(return_value=None)),  # Latest weight
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Existing milestone
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # Verify adherence milestone
    adherence_milestones = [m for m in milestones if m["type"] == "adherence"]
    assert len(adherence_milestones) >= 1
    assert any("30 days" in m["description"] and "80%" in m["description"] for m in adherence_milestones)


@pytest.mark.asyncio
async def test_no_duplicate_milestones(progress_service, mock_db_session):
    """Test that duplicate milestones are not created."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Mock existing 7-day streak milestone
    existing_milestone = MagicMock()
    existing_milestone.milestone_description = "7 days"

    # Mock 7 consecutive days again
    today = date.today()
    workout_dates = [today - timedelta(days=i) for i in range(7)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = workout_dates

    mock_existing_result = MagicMock()
    mock_existing_result.scalars.return_value.all.return_value = [existing_milestone]

    mock_db_session.execute.side_effect = [
        mock_result,  # Workout dates
        mock_existing_result,  # Existing 7-day streak milestone found
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # Should not return duplicate milestone
    assert len([m for m in milestones if "7 days" in m["description"]]) == 0


@pytest.mark.asyncio
async def test_no_milestones_with_insufficient_data(progress_service, mock_db_session):
    """Test that no milestones are detected with insufficient data."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Mock only 3 days of workouts
    today = date.today()
    workout_dates = [today - timedelta(days=i) for i in range(3)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = workout_dates

    mock_db_session.execute.side_effect = [
        mock_result,
        MagicMock(scalar=MagicMock(return_value=3)),  # Only 3 workouts
        MagicMock(scalar=MagicMock(return_value=None)),  # No weight data
        MagicMock(scalar=MagicMock(return_value=None)),
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # No milestones should be detected (3 days < 7, 3 workouts < 10, no weight data)
    assert len(milestones) == 0


@pytest.mark.asyncio
async def test_record_milestone_achievement(progress_service, mock_db_session):
    """Test recording a milestone achievement."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    milestone_data = {
        "type": "streak",
        "description": "7 days",
        "message": "You've completed 7 consecutive days of workouts!",
    }

    # Call record_milestone_achievement
    await progress_service.record_milestone_achievement(user_id, fitness_plan_id, milestone_data)

    # Verify that session.add was called
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

    # Verify the added object
    added_record = mock_db_session.add.call_args[0][0]
    assert added_record.user_id == user_id
    assert added_record.fitness_plan_id == fitness_plan_id
    assert added_record.record_type == "milestone"
    assert added_record.milestone_type == "streak"
    assert added_record.milestone_description == "7 days"


@pytest.mark.asyncio
async def test_multiple_milestone_types_detected(progress_service, mock_db_session):
    """Test detecting multiple milestone types in one check."""
    user_id = uuid4()
    fitness_plan_id = uuid4()

    # Mock data that triggers multiple milestones:
    # - 30 consecutive days (streak)
    # - 50 total workouts (workouts)
    # - 10 lbs weight loss (weight_loss)
    today = date.today()
    workout_dates = [today - timedelta(days=i) for i in range(30)]

    mock_dates_result = MagicMock()
    mock_dates_result.scalars.return_value.all.return_value = workout_dates

    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 50

    mock_initial_weight = MagicMock()
    mock_initial_weight.scalar.return_value = 200.0

    mock_latest_weight = MagicMock()
    mock_latest_weight.scalar.return_value = 190.0

    mock_db_session.execute.side_effect = [
        mock_dates_result,  # Workout dates
        mock_count_result,  # Workout count
        mock_initial_weight,  # Initial weight
        mock_latest_weight,  # Latest weight
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # No existing milestones
    ]

    milestones = await progress_service.detect_milestones(user_id, fitness_plan_id)

    # Should detect multiple milestone types
    milestone_types = {m["type"] for m in milestones}
    assert "streak" in milestone_types or "adherence" in milestone_types
    assert "workouts" in milestone_types
    assert "weight_loss" in milestone_types
    assert len(milestones) >= 3

