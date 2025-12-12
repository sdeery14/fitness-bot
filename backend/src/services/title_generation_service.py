"""Service for generating conversation titles using OpenAI Agents SDK."""
from agents import Agent, Runner

from src.ai.agent import create_model_settings


def create_title_generation_agent() -> Agent:
    """Create an agent that generates concise conversation titles.
    
    Returns:
        Agent configured for title generation
    """
    instructions = """You generate concise, descriptive titles for fitness coaching conversations.

Your role is to:
1. Analyze the first message exchange between user and AI coach
2. Create a 3-5 word title that captures the conversation topic
3. Make it specific and descriptive (avoid generic titles like "Fitness Chat")

Guidelines:
- Keep it short: 3-5 words maximum
- Be specific: "Muscle Building Plan" not "Fitness Help"
- Focus on the main topic or goal
- Use title case
- NO quotes, NO punctuation at the end
- Examples:
  * "Weight Loss Journey"
  * "Build Muscle at Home"
  * "Marathon Training Plan"
  * "Vegan Diet Questions"
  * "Shoulder Injury Recovery"

Output ONLY the title, nothing else."""

    return Agent(
        name="Title Generator",
        instructions=instructions,
        model_settings=create_model_settings(),
        tools=[],  # No tools needed for title generation
    )


async def generate_conversation_title(user_message: str, ai_response: str) -> str:
    """Generate a concise title for a conversation based on the first exchange.

    Args:
        user_message: The user's first message
        ai_response: The AI's first response

    Returns:
        A 3-5 word descriptive title
    """
    try:
        agent = create_title_generation_agent()

        conversation_context = f"User: {user_message}\n\nAssistant: {ai_response}"

        # Run agent using Runner
        result = await Runner.run(
            starting_agent=agent,
            input=conversation_context,
            session=None,
        )

        title = result.final_output.strip()
        # Remove quotes if present
        title = title.strip('"\'')
        # Truncate to 255 chars if needed
        return title[:255] if len(title) > 255 else title

    except Exception as e:
        # Fallback to generic title if generation fails
        print(f"Error generating title: {e}")
        return "New Conversation"
