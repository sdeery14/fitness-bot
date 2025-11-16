"""AI agent modules for fitness plan generation.

Multi-agent architecture using OpenAI Agents SDK:
- Conversation Agent: User interaction and requirement extraction
- Fitness Plan Agent: Plan coordination and orchestration
- Workout Plan Agent: Exercise selection from curated database
- Meal Plan Agent: Meal generation with USDA nutritional data
"""
from src.ai.agent import (
    MODEL_CONFIGS,
    PlanContext,
    UserContext,
    agent_registry,
    create_model_settings,
    get_model_config,
)

__all__ = [
    "MODEL_CONFIGS",
    "PlanContext",
    "UserContext",
    "agent_registry",
    "create_model_settings",
    "get_model_config",
]
