"""Agent runner wrappers for MLflow evaluation.

These functions wrap the actual fitness agents to provide a clean interface for MLflow's
evaluation framework. Each runner:
1. Takes inputs from the MLflow dataset
2. Executes the appropriate agent
3. Returns outputs in a format suitable for judge evaluation
"""

import json
from typing import Any
from agents import Runner

from src.ai.app_agents.workout_phase_agent import workout_phase_agent
from src.ai.app_agents.intake_specialist_agent import intake_specialist_agent
from src.ai.app_agents.fitness_coach_agent import fitness_coach_agent


# ============================================================================
# Workout Phase Agent Runner
# ============================================================================

async def run_workout_phase_agent(**inputs) -> dict[str, Any]:
    """Run workout_phase_agent with MLflow dataset inputs.
    
    Args:
        **inputs: Keyword args containing:
            - workout_plan_description: Overall strategy (str)
            - phase_number: Phase number (int)
            - phase_name: Phase name (str)
            - phase_objectives: List of objectives (list[str])
            - phase_duration_weeks: Duration (int)
            - fitness_level: User fitness level (str)
            - equipment_access: Available equipment (list[str])
            - workout_frequency: Days per week (int)
    
    Returns:
        Dict with generated PhaseWorkoutDetails (workouts, workout_cycle, etc.)
    """
    # Build prompt for workout phase agent
    prompt = f"""Generate workout details for this phase:

Phase Context:
- Phase {inputs['phase_number']}: {inputs['phase_name']}
- Duration: {inputs['phase_duration_weeks']} weeks
- Objectives: {', '.join(inputs['phase_objectives'])}

Overall Workout Plan:
{inputs['workout_plan_description']}

User Context:
- Fitness Level: {inputs['fitness_level']}
- Workout Frequency: {inputs['workout_frequency']} days/week
- Equipment: {', '.join(inputs['equipment_access'])}

Generate the specific workout cycle, intensity guidance, volume notes, and progression strategy for this phase."""

    # Run agent
    result = await Runner.run(
        starting_agent=workout_phase_agent,
        input=prompt,
        session=None,
    )
    
    # Extract output - should be PhaseWorkoutDetails
    output = result.final_output
    
    # Convert to dict for MLflow (Pydantic model -> dict)
    if hasattr(output, 'model_dump'):
        output_dict = output.model_dump()
    elif hasattr(output, 'dict'):
        output_dict = output.dict()
    else:
        output_dict = output
    
    return output_dict


def run_workout_phase_agent_sync(**inputs) -> dict[str, Any]:
    """Synchronous wrapper for workout phase agent (for MLflow compatibility).
    
    MLflow's evaluate function expects synchronous predict functions.
    This wrapper runs the async agent in a new event loop.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_workout_phase_agent(**inputs))


# ============================================================================
# Intake Agent Runner (Conversation)
# ============================================================================

async def run_intake_agent(**inputs) -> dict[str, Any]:
    """Run intake_specialist_agent with MLflow dataset inputs.
    
    Args:
        **inputs: Keyword args containing:
            - messages: List of conversation messages (list[dict])
                Each message: {"role": "user", "content": "..."}
    
    Returns:
        Dict with agent response and metadata
    """
    # Extract user message (last message should be user)
    messages = inputs.get('messages', [])
    if not messages:
        return {"response": "No input provided", "error": True}
    
    # Build conversation prompt from messages
    user_message = messages[-1]['content']
    
    # For intake agent, just pass the user's message
    # (In real system, we'd load conversation history if available)
    
    # Run agent
    result = await Runner.run(
        starting_agent=intake_specialist_agent,
        input=user_message,
        session=None,
    )
    
    # Extract agent response
    response_text = result.final_output if isinstance(result.final_output, str) else str(result.final_output)
    
    # Check if agent tried to use tools
    tool_calls = []
    if hasattr(result, 'all_messages'):
        for msg in result.all_messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls.extend([tc.function.name for tc in msg.tool_calls])
    
    return {
        "response": response_text,
        "tool_calls_made": tool_calls,
        "conversation_complete": "build_fitness_plan" in tool_calls,
    }


def run_intake_agent_sync(**inputs) -> dict[str, Any]:
    """Synchronous wrapper for intake agent."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_intake_agent(**inputs))


# ============================================================================
# Fitness Coach Agent Runner (Conversation)
# ============================================================================

async def run_fitness_coach_agent(**inputs) -> dict[str, Any]:
    """Run fitness_coach_agent with MLflow dataset inputs.
    
    Args:
        **inputs: Keyword args containing:
            - messages: List of conversation messages (list[dict])
            - user_context: Dict with plan context (optional)
                {
                    "has_active_plan": bool,
                    "plan_name": str,
                    "current_phase": str,
                    "current_week": int
                }
    
    Returns:
        Dict with agent response and metadata
    """
    # Extract user message
    messages = inputs.get('messages', [])
    if not messages:
        return {"response": "No input provided", "error": True}
    
    user_message = messages[-1]['content']
    user_context = inputs.get('user_context', {})
    
    # Build enriched prompt with context
    if user_context.get('has_active_plan'):
        enriched_message = f"""[User has active plan: {user_context.get('plan_name')}]
[Current phase: {user_context.get('current_phase')}]
[Week: {user_context.get('current_week')}]

User message: {user_message}"""
    else:
        enriched_message = user_message
    
    # Run agent
    result = await Runner.run(
        starting_agent=fitness_coach_agent,
        input=enriched_message,
        session=None,
    )
    
    # Extract agent response
    response_text = result.final_output if isinstance(result.final_output, str) else str(result.final_output)
    
    # Check if agent used tools
    tool_calls = []
    if hasattr(result, 'all_messages'):
        for msg in result.all_messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls.extend([tc.function.name for tc in msg.tool_calls])
    
    return {
        "response": response_text,
        "tool_calls_made": tool_calls,
        "used_query_tool": "query_fitness_plan" in tool_calls,
        "used_update_tool": "update_fitness_plan" in tool_calls,
    }


def run_fitness_coach_agent_sync(**inputs) -> dict[str, Any]:
    """Synchronous wrapper for fitness coach agent."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_fitness_coach_agent(**inputs))


async def run_meal_phase_agent(**inputs) -> Dict[str, Any]:
    """
    Execute the meal phase agent.
    Accepts keyword arguments matching the dataset inputs.
    Returns the PhaseMealDetails output as a dictionary.
    """
    from src.ai.app_agents.meal_phase_agent import meal_phase_agent
    
    result = await meal_phase_agent.run(**inputs)
    
    # Return structured output (PhaseMealDetails)
    if hasattr(result, "output"):
        return result.output.model_dump()
    return {"error": "No output from meal_phase_agent"}


def run_meal_phase_agent_sync(**inputs) -> Dict[str, Any]:
    """Synchronous wrapper for meal phase agent evaluation."""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_meal_phase_agent(**inputs))


# ============================================================================
# Registry: Map agent names to runner functions
# ============================================================================

AGENT_RUNNERS = {
    "workout_phase_agent": run_workout_phase_agent_sync,
    "intake_agent": run_intake_agent_sync,
    "fitness_coach_agent": run_fitness_coach_agent_sync,
    "meal_phase_agent": run_meal_phase_agent_sync,
}


def get_agent_runner(agent_name: str):
    """Get the appropriate runner function for an agent.
    
    Args:
        agent_name: One of 'workout_phase_agent', 'intake_agent', 'fitness_coach_agent'
    
    Returns:
        Callable runner function compatible with mlflow.genai.evaluate
    """
    runner = AGENT_RUNNERS.get(agent_name)
    if runner is None:
        raise ValueError(f"Unknown agent: {agent_name}. Expected one of {list(AGENT_RUNNERS.keys())}")
    
    return runner
