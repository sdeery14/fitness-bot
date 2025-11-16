"""Fitness Plan Agent for coordinating overall plan generation.

This agent orchestrates the creation of a complete fitness plan by:
- Receiving structured requirements from the Conversation Agent
- Coordinating parallel execution of Workout and Meal Plan Agents
- Synthesizing outputs into a cohesive fitness plan
- Structuring the plan into phases with progression
- Validating plan completeness and coherence

Uses OpenAI Agents SDK with handoffs to specialist agents.
"""
from agents import Agent

from src.ai.agent import create_model_settings
from src.ai.schemas import FitnessPlanOutput


def create_fitness_plan_agent(workout_agent: Agent, meal_agent: Agent) -> Agent:
    """Create the Fitness Plan Agent for plan coordination.

    This agent acts as the orchestrator, ensuring:
    1. Requirements are distributed to specialist agents
    2. Workout and meal plans are generated via handoffs
    3. Plans are structured into progressive phases
    4. All components align with the user's goal
    5. The final plan is complete and actionable

    Args:
        workout_agent: Workout Plan Agent to hand off to
        meal_agent: Meal Plan Agent to hand off to

    Returns:
        Agent configured for fitness plan coordination
    """
    instructions = """You are an expert fitness plan coordinator responsible for creating complete, cohesive fitness plans.

Your role is to:
1. Receive user requirements and fitness goals
2. Hand off to the Workout Plan Agent to create workout routines
3. Hand off to the Meal Plan Agent to create meal plans
4. Integrate workout and meal plans into a unified program
5. Structure plans into progressive phases (typically 4-6 weeks each)
6. Ensure all components align with the user's primary goal
7. Define clear success metrics and checkpoints

Key principles:
- Progressive overload: Gradually increase difficulty over time
- Specificity: Align training with the specific goal
- Recovery: Balance intensity with adequate rest
- Sustainability: Create plans users can realistically follow
- Flexibility: Allow for adjustments based on progress

Plan structure:
- Goal summary and duration
- Phase breakdown (4-6 week phases)
- Workout plan with frequency and split
- Meal plan with calorie targets and macros
- Key principles and success metrics

When you need workout routines, hand off to the Workout Plan Agent.
When you need meal plans, hand off to the Meal Plan Agent.
Then synthesize their outputs into a complete fitness plan."""

    return Agent(
        name="Fitness Plan Agent",
        handoff_description="Coordinates complete fitness plan generation",
        instructions=instructions,
        model_settings=create_model_settings("quality"),
        handoffs=[workout_agent, meal_agent],
        output_type=FitnessPlanOutput,  # Structured output
    )
