"""Simple tests for _apply_update logic without database."""

import pytest
from src.services.plan_service import PlanService


class MockObject:
    """Mock object for testing field path parsing."""
    def __init__(self):
        self.duration_weeks = 12
        self.goal_description = "Lose weight"
        self.phases = [
            type('obj', (object,), {'duration_weeks': 4, 'objectives': 'Build base'})(),
            type('obj', (object,), {'duration_weeks': 4, 'objectives': 'Increase intensity'})(),
        ]
        self.workout_plans = [
            type('obj', (object,), {'frequency_per_week': 3, 'progression_strategy': 'linear'})(),
        ]


def test_apply_update_simple_field():
    """Test updating a simple field."""
    service = PlanService(None)  # No DB needed
    obj = MockObject()
    
    service._apply_update(obj, "duration_weeks", 16, "set")
    
    assert obj.duration_weeks == 16


def test_apply_update_array_index():
    """Test updating a field in an array element."""
    service = PlanService(None)
    obj = MockObject()
    
    service._apply_update(obj, "phases[0].duration_weeks", 6, "set")
    
    assert obj.phases[0].duration_weeks == 6
    assert obj.phases[1].duration_weeks == 4  # Unchanged


def test_apply_update_increment():
    """Test increment operation."""
    service = PlanService(None)
    obj = MockObject()
    
    service._apply_update(obj, "duration_weeks", 4, "increment")
    
    assert obj.duration_weeks == 16  # 12 + 4


def test_apply_update_nested_array():
    """Test updating nested array path."""
    service = PlanService(None)
    obj = MockObject()
    
    service._apply_update(obj, "workout_plans[0].frequency_per_week", 5, "set")
    
    assert obj.workout_plans[0].frequency_per_week == 5


def test_apply_update_invalid_field():
    """Test error handling for invalid field."""
    service = PlanService(None)
    obj = MockObject()
    
    # Setting a non-existent attribute will succeed (Python allows it)
    # But trying to access it in a path will fail
    with pytest.raises(ValueError, match="Attribute 'nonexistent' not found"):
        service._apply_update(obj, "nonexistent.sub_field", "value", "set")


def test_apply_update_invalid_index():
    """Test error handling for invalid array index."""
    service = PlanService(None)
    obj = MockObject()
    
    with pytest.raises(ValueError, match="Index 5 out of range"):
        service._apply_update(obj, "phases[5].duration_weeks", 6, "set")


def test_apply_update_invalid_operation():
    """Test error handling for invalid operation."""
    service = PlanService(None)
    obj = MockObject()
    
    with pytest.raises(ValueError, match="Unsupported operation: invalid"):
        service._apply_update(obj, "duration_weeks", 16, "invalid")
