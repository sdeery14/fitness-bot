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


def create_model_settings() -> ModelSettings:
    """Create ModelSettings using only the model from environment.

    All agents use the same model specified in MODEL_NAME environment variable.
    No presets or token limits - let the model use its default limits.

    Returns:
        ModelSettings instance configured with env model
    """
    return ModelSettings(
        model=settings.MODEL_NAME,  # Use MODEL_NAME from environment
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

