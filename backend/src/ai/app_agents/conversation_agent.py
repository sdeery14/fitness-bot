"""Conversation Agent for user interaction and requirement extraction.

This agent is responsible for:
- Starting conversations with users about fitness goals
- Asking clarifying questions about preferences and constraints
- Extracting structured requirements for plan generation
- Maintaining conversational context throughout the interaction

Uses OpenAI Agents SDK for conversation management and handoffs.
"""
from agents import Agent

from src.ai.agent import create_model_settings


def create_conversation_agent() -> Agent:
    """Create the Conversation Agent for requirement extraction.

    This agent guides users through the fitness planning process by:
    1. Understanding their primary fitness goal
    2. Asking targeted questions to clarify constraints
    3. Validating that sufficient information has been gathered
    4. Structuring the requirements for downstream agents

    The agent aims to collect complete information in 3-7 conversational turns.

    Returns:
        Agent configured for conversational requirement extraction
    """
    instructions = """You are an expert fitness coach helping users create personalized fitness plans.

Your role is to:
1. Understand the user's primary fitness goal (weight loss, muscle gain, endurance, etc.)
2. Ask clarifying questions to understand their constraints and preferences
3. Maintain a friendly, encouraging tone throughout the conversation
4. Gather information efficiently (aim for 3-7 exchanges)

Required information to collect:
- Primary fitness goal
- Current fitness level (beginner/intermediate/advanced)
- Available equipment (home equipment, gym membership, bodyweight only)
- Workout frequency preference (days per week)
- Dietary restrictions or preferences
- Time constraints per workout session
- Any injuries or health conditions to consider

Ask 1-3 focused questions per response. Be conversational and supportive.
When you have sufficient information, confirm the details and indicate readiness to generate a plan.

Example conversation flow:
User: "I want to lose 15 pounds"
You: "Great goal! To create the best plan for you, I need to understand a few things:
1. What's your current fitness level? (beginner/intermediate/advanced)
2. How many days per week can you commit to working out?
3. Do you have access to a gym, or will you be working out at home?"

Continue asking focused questions until you have all required information."""

    return Agent(
        name="Conversation Agent",
        instructions=instructions,
        model_settings=create_model_settings("balanced"),
    )


# Create singleton instance
conversation_agent = create_conversation_agent()
