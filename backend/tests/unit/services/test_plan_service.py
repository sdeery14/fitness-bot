"""Unit tests for PlanService improvement suggestions logic."""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.plan_service import PlanService


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def plan_service(mock_db):
    """Plan service with mocked database."""
    return PlanService(mock_db)


class TestAnalyzeProgressForSuggestions:
    """Test suite for analyze_progress_for_suggestions method."""

    async def test_high_adherence_returns_positive_metrics(self, plan_service, mock_db):
        """Test that high adherence (80%+) is correctly calculated."""
        # Arrange
        user_id = uuid4()
        fitness_plan_id = uuid4()

        # Mock 14 days of high adherence (12 out of 14 days = 85.7%)
        mock_progress_entries = []
        for i in range(14):
            entry_date = date.today() - timedelta(days=i)
            # 12 days with both workout and meal completed
            if i < 12:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=True,
                        meal_completed=True,
                    )
                )
            else:
                # 2 days with nothing completed
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=False,
                        meal_completed=False,
                    )
                )

        # Setup mock response
        mock_db.execute.return_value = AsyncMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_progress_entries)))
        )

        # Act
        result = await plan_service.analyze_progress_for_suggestions(user_id, fitness_plan_id)

        # Assert
        assert result["overall_adherence"] >= 80.0
        assert result["workout_adherence"] >= 80.0
        assert result["meal_adherence"] >= 80.0

    async def test_low_adherence_returns_low_metrics(self, plan_service, mock_db):
        """Test that low adherence (<50%) is correctly calculated."""
        # Arrange
        user_id = uuid4()
        fitness_plan_id = uuid4()

        # Mock 14 days of low adherence (5 out of 14 days = 35.7%)
        mock_progress_entries = []
        for i in range(14):
            entry_date = date.today() - timedelta(days=i)
            # Only 5 days with both completed
            if i < 5:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=True,
                        meal_completed=True,
                    )
                )
            else:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=False,
                        meal_completed=False,
                    )
                )

        mock_db.execute.return_value = AsyncMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_progress_entries)))
        )

        # Act
        result = await plan_service.analyze_progress_for_suggestions(user_id, fitness_plan_id)

        # Assert
        assert result["overall_adherence"] < 50.0

    async def test_identifies_weak_days_correctly(self, plan_service, mock_db):
        """Test that weak days (Monday, Friday) are identified."""
        # Arrange
        user_id = uuid4()
        fitness_plan_id = uuid4()

        # Mock 30 days with Mondays and Fridays being weak
        mock_progress_entries = []
        for i in range(30):
            entry_date = date.today() - timedelta(days=i)
            day_of_week = entry_date.strftime("%A")

            # Mondays and Fridays have lower adherence
            if day_of_week in ["Monday", "Friday"]:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=False,
                        meal_completed=False,
                    )
                )
            else:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=True,
                        meal_completed=True,
                    )
                )

        mock_db.execute.return_value = AsyncMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_progress_entries)))
        )

        # Act
        result = await plan_service.analyze_progress_for_suggestions(user_id, fitness_plan_id)

        # Assert
        assert "patterns" in result
        assert "weak_days" in result["patterns"]
        weak_days = result["patterns"]["weak_days"]
        assert len(weak_days) >= 1
        weak_day_names = [d["day"] for d in weak_days]
        assert any(day in ["Monday", "Friday"] for day in weak_day_names)


class TestGenerateImprovementRecommendations:
    """Test suite for generate_improvement_recommendations method."""

    async def test_low_adherence_suggests_simplification(self, plan_service, mock_db):
        """Test that low adherence (<50%) triggers schedule simplification recommendations."""
        # Arrange
        user_id = uuid4()
        fitness_plan_id = uuid4()

        # Mock fitness plan
        mock_plan = MagicMock()
        mock_plan.id = fitness_plan_id
        mock_plan.start_date = date.today() - timedelta(days=20)

        # Mock low adherence progress (30%)
        mock_progress_entries = []
        for i in range(14):
            entry_date = date.today() - timedelta(days=i)
            # Only 4 days completed (30%)
            if i < 4:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=True,
                        meal_completed=True,
                    )
                )
            else:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=False,
                        meal_completed=False,
                    )
                )

        # Setup mock responses
        mock_db.execute.side_effect = [
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_progress_entries)))),
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
        ]

        # Act
        result = await plan_service.generate_improvement_recommendations(user_id, fitness_plan_id)

        # Assert
        assert "recommendations" in result
        recommendations = result["recommendations"]
        assert len(recommendations) > 0

        # Should have a recommendation for schedule simplification
        categories = [r["category"] for r in recommendations]
        assert "Schedule Simplification" in categories

        # Check for high priority recommendation
        priorities = [r["priority"] for r in recommendations]
        assert "high" in priorities

    async def test_high_adherence_suggests_progression(self, plan_service, mock_db):
        """Test that high adherence (80%+) triggers progressive overload recommendations."""
        # Arrange
        user_id = uuid4()
        fitness_plan_id = uuid4()

        # Mock fitness plan
        mock_plan = MagicMock()
        mock_plan.id = fitness_plan_id
        mock_plan.start_date = date.today() - timedelta(days=20)

        # Mock high adherence progress (85%)
        mock_progress_entries = []
        for i in range(14):
            entry_date = date.today() - timedelta(days=i)
            # 12 days completed (85%)
            if i < 12:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=True,
                        meal_completed=True,
                    )
                )
            else:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=False,
                        meal_completed=False,
                    )
                )

        # Setup mock responses
        mock_db.execute.side_effect = [
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_progress_entries)))),
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
        ]

        # Act
        result = await plan_service.generate_improvement_recommendations(user_id, fitness_plan_id)

        # Assert
        assert "recommendations" in result
        recommendations = result["recommendations"]
        assert len(recommendations) > 0

        # Should have a recommendation for progressive overload
        categories = [r["category"] for r in recommendations]
        assert "Progressive Overload" in categories

    async def test_workout_meal_disparity_detected(self, plan_service, mock_db):
        """Test that significant disparity between workout and meal adherence is detected."""
        # Arrange
        user_id = uuid4()
        fitness_plan_id = uuid4()

        # Mock fitness plan
        mock_plan = MagicMock()
        mock_plan.id = fitness_plan_id
        mock_plan.start_date = date.today() - timedelta(days=20)

        # Mock progress with high workout but low meal adherence
        mock_progress_entries = []
        for i in range(14):
            entry_date = date.today() - timedelta(days=i)
            # 12 days workout completed (85%)
            # 4 days meal completed (30%)
            if i < 12:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=True,
                        meal_completed=i < 4,  # Only first 4 days
                    )
                )
            else:
                mock_progress_entries.append(
                    MagicMock(
                        progress_date=entry_date,
                        workout_completed=False,
                        meal_completed=False,
                    )
                )

        # Setup mock responses
        mock_db.execute.side_effect = [
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_progress_entries)))),
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_plan)),
        ]

        # Act
        result = await plan_service.generate_improvement_recommendations(user_id, fitness_plan_id)

        # Assert
        assert "recommendations" in result
        recommendations = result["recommendations"]
        assert len(recommendations) > 0

        # Should have a recommendation for nutrition planning
        categories = [r["category"] for r in recommendations]
        assert "Nutrition Planning" in categories

        # Should be high priority
        nutrition_recs = [r for r in recommendations if r["category"] == "Nutrition Planning"]
        assert nutrition_recs[0]["priority"] == "high"

