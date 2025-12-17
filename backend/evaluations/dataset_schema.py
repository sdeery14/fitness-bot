"""Evaluation dataset schema for AI agents.

Each test case consists of:
- input: The input to the agent
- expected_output: What we expect the agent to produce
- metadata: Context about what we're testing
- evaluation_criteria: Specific criteria for judging this test case
"""
from typing import Any, Literal
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """Base test case structure for agent evaluation."""
    
    id: str = Field(..., description="Unique identifier for this test case")
    description: str = Field(..., description="Human-readable description of what this tests")
    input: dict[str, Any] = Field(..., description="Input data for the agent")
    expected_output: dict[str, Any] = Field(..., description="Expected agent output/behavior")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    evaluation_criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Specific criteria for LLM-as-a-judge to evaluate"
    )


class WorkoutPhaseTestCase(TestCase):
    """Test case for the workout phase generation agent."""
    
    input: dict[str, Any] = Field(
        ...,
        description="""Input should contain:
        - phase_name: str
        - phase_number: int
        - duration_weeks: int
        - objectives: list[str]
        - user_profile: dict (fitness_level, equipment, etc.)
        - workout_preferences: dict (frequency, duration, etc.)
        """
    )
    
    expected_output: dict[str, Any] = Field(
        ...,
        description="""Expected output should validate:
        - workout_count: int (correct number of workouts generated)
        - workout_types: list[str] (appropriate types: strength/cardio/hybrid)
        - intensity_levels: list[str] (appropriate for phase)
        - exercises_per_workout: dict[str, int] (reasonable exercise count)
        - equipment_match: bool (uses only available equipment)
        - duration_match: bool (workouts fit time constraints)
        """
    )
    
    evaluation_criteria: dict[str, Any] = Field(
        default_factory=lambda: {
            "output_quality": {
                "weight": 0.3,
                "aspects": [
                    "Workouts are appropriate for fitness level",
                    "Exercise selection matches phase objectives",
                    "Progression is logical within the phase",
                    "Volume/intensity is appropriate"
                ]
            },
            "tool_selection": {
                "weight": 0.2,
                "aspects": [
                    "Uses generate_workout_phase tool correctly",
                    "Provides all required parameters",
                    "Parameters are valid and sensible"
                ]
            },
            "response_quality": {
                "weight": 0.3,
                "aspects": [
                    "Clear explanation of workout structure",
                    "Addresses user's fitness level and goals",
                    "Provides helpful context about the phase"
                ]
            },
            "safety": {
                "weight": 0.2,
                "aspects": [
                    "Appropriate warmup/cooldown included",
                    "Exercise selection avoids injury risk for level",
                    "Volume/intensity doesn't cause overtraining",
                    "Respects any mentioned limitations"
                ]
            }
        }
    )


class IntakeTestCase(TestCase):
    """Test case for the intake/onboarding agent."""
    
    evaluation_criteria: dict[str, Any] = Field(
        default_factory=lambda: {
            "information_gathering": {
                "weight": 0.3,
                "aspects": [
                    "Asks all essential questions",
                    "Questions are clear and specific",
                    "Adapts based on user responses",
                    "Doesn't ask unnecessary questions"
                ]
            },
            "response_quality": {
                "weight": 0.3,
                "aspects": [
                    "Friendly and professional tone",
                    "Explains why information is needed",
                    "Provides helpful context",
                    "Efficient conversation flow"
                ]
            },
            "plan_generation": {
                "weight": 0.3,
                "aspects": [
                    "Generated plan matches user goals",
                    "Phases are appropriate for duration",
                    "Workout frequency matches availability",
                    "Nutrition targets are reasonable"
                ]
            },
            "safety": {
                "weight": 0.1,
                "aspects": [
                    "Identifies and respects injuries/limitations",
                    "Sets realistic expectations",
                    "Doesn't make unrealistic promises"
                ]
            }
        }
    )


class FitnessCoachTestCase(TestCase):
    """Test case for the fitness coach agent (query/update/build)."""
    
    test_type: Literal["query", "update", "build"] = Field(
        ...,
        description="Type of interaction being tested"
    )
    
    evaluation_criteria: dict[str, Any] = Field(
        default_factory=lambda: {
            "tool_selection": {
                "weight": 0.3,
                "aspects": [
                    "Chooses correct tool (query/update/build)",
                    "Uses query_fitness_plan before updates",
                    "Provides correct field paths for updates",
                    "Validates array indices before bulk updates"
                ]
            },
            "response_quality": {
                "weight": 0.3,
                "aspects": [
                    "Answers user question accurately",
                    "Provides helpful context",
                    "Coaching tone is supportive",
                    "Explanations are clear"
                ]
            },
            "output_quality": {
                "weight": 0.3,
                "aspects": [
                    "Plan modifications are appropriate",
                    "Changes match user request",
                    "Schedule regeneration works correctly",
                    "Versioning preserves history"
                ]
            },
            "safety": {
                "weight": 0.1,
                "aspects": [
                    "Doesn't make unsafe modifications",
                    "Warns about potential issues",
                    "Maintains plan integrity"
                ]
            }
        }
    )


class EvaluationDataset(BaseModel):
    """Collection of test cases for agent evaluation."""
    
    name: str = Field(..., description="Dataset name")
    version: str = Field(..., description="Dataset version (e.g., '1.0.0')")
    description: str = Field(..., description="What this dataset tests")
    agent_name: str = Field(..., description="Which agent this evaluates")
    test_cases: list[TestCase] = Field(..., description="List of test cases")
    
    def to_mlflow_format(self) -> dict:
        """Convert to MLflow evaluation dataset format."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "data": [tc.model_dump() for tc in self.test_cases]
        }
