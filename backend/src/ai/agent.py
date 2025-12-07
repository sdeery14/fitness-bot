"""Base agent initialization and configuration for AI-powered fitness planning.

This module provides the foundation for the multi-agent orchestration system using
the OpenAI Agents SDK:
- Conversation Agent: Extracts user requirements, asks clarifying questions
- Fitness Plan Agent: Coordinates overall plan generation
- Workout Plan Agent: Selects exercises from curated database
- Meal Plan Agent: Generates meals using USDA nutritional data

Architecture:
    Triage Agent (Conversation) → Fitness Plan Agent → Handoffs to:
        - Workout Plan Agent (specialist)
        - Meal Plan Agent (specialist)

State Management:
    Uses Sessions for automatic conversation history management
    Storage references (Redis keys, PostgreSQL IDs) passed via context
"""
from typing import Any

from agents import Agent, ModelSettings
from pydantic import BaseModel

from src.config import settings


# Model configuration presets for different use cases
# Note: The "model" field in each preset is now overridden by settings.MODEL_NAME from env
MODEL_CONFIGS = {
    "fast": {
        "model": "gpt-4o-mini",  # Overridden by settings.MODEL_NAME
        "temperature": 0.7,
        "max_tokens": 1000,
        "description": "Fast, cost-effective responses for simple tasks",
    },
    "balanced": {
        "model": "gpt-4o",  # Overridden by settings.MODEL_NAME
        "temperature": 0.7,
        "max_tokens": 2000,
        "description": "Balanced speed and quality for most tasks",
    },
    "quality": {
        "model": "gpt-4o",  # Overridden by settings.MODEL_NAME
        "temperature": 0.5,
        "max_tokens": 4000,
        "description": "High-quality responses for complex planning",
    },
    "creative": {
        "model": "gpt-4o",  # Overridden by settings.MODEL_NAME
        "temperature": 1.0,
        "max_tokens": 2000,
        "description": "More creative responses for meal/workout variations",
    },
}


def get_model_config(preset: str = "balanced") -> dict[str, Any]:
    """Get model configuration by preset name.

    Args:
        preset: One of "fast", "balanced", "quality", "creative"

    Returns:
        Model configuration dict

    Raises:
        ValueError: If preset name is invalid
    """
    if preset not in MODEL_CONFIGS:
        raise ValueError(
            f"Invalid preset '{preset}'. Choose from: {', '.join(MODEL_CONFIGS.keys())}"
        )
    return MODEL_CONFIGS[preset].copy()


def create_model_settings(preset: str = "balanced") -> ModelSettings:
    """Create ModelSettings from a preset configuration.

    Uses the MODEL_NAME from environment settings for all agents,
    while preserving temperature and token settings from the preset.

    Args:
        preset: Configuration preset name

    Returns:
        ModelSettings instance configured for the preset with env model
    """
    config = get_model_config(preset)
    return ModelSettings(
        model=settings.MODEL_NAME,  # Use MODEL_NAME from environment
        temperature=config["temperature"],
        max_tokens=config.get("max_tokens"),
    )


# Context models for passing data between agents
class UserContext(BaseModel):
    """Context data passed to agents about the user."""

    user_id: str
    email: str | None = None
    preferences: dict[str, Any] = {}


class PlanContext(BaseModel):
    """Context data for plan generation."""

    plan_id: str | None = None
    requirements: dict[str, Any] = {}
    user_context: UserContext
    conversation_history: list[dict[str, str]] = []  # List of {"role": "user|assistant", "content": "..."}


# Agent registry for managing agent instances
agent_registry: dict[str, Agent] = {}


def register_agent(name: str, agent: Agent) -> None:
    """Register an agent instance for reuse.

    Args:
        name: Agent identifier
        agent: Agent instance from OpenAI Agents SDK
    """
    agent_registry[name] = agent


def get_agent(name: str) -> Agent | None:
    """Retrieve a registered agent.

    Args:
        name: Agent identifier

    Returns:
        Agent instance or None if not found
    """
    return agent_registry.get(name)


def clear_agent_registry() -> None:
    """Clear all registered agents (useful for testing)."""
    agent_registry.clear()


# Verify OpenAI API key is configured
if not settings.OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY must be set in environment variables or .env file"
    )

