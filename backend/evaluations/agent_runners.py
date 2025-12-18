"""Agent runner wrappers for MLflow evaluation.

These functions wrap the actual fitness agents to provide a clean interface for MLflow's
evaluation framework. Each runner:
1. Takes inputs from the MLflow dataset
2. Executes the appropriate agent
3. Returns outputs in a format suitable for judge evaluation
"""

import asyncio
import json
from typing import Any
from agents import Runner

from src.ai.app_agents.workout_phase_agent import workout_phase_agent
from src.ai.app_agents.intake_specialist_agent import intake_specialist_agent
from src.ai.app_agents.fitness_coach_agent import fitness_coach_agent
from src.ai.app_agents.query_agent import query_agent
from src.ai.tools.query_tools import initialize_mcp_server, _mcp_server


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
    This wrapper runs the async agent using asyncio.run().
    """
    import asyncio
    
    return asyncio.run(run_workout_phase_agent(**inputs))


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
    
    return asyncio.run(run_intake_agent(**inputs))


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
    from uuid import uuid4
    from src.ai.tools.plan_tools import set_plan_tools_context, clear_plan_tools_context
    
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
    
    # Set context for tools using real test user from database
    # User ID: fa19dc54-a35b-4aab-adf8-816933f96fa4 (created by setup_test_user.py)
    from uuid import UUID
    from src.database import get_db
    
    test_user_id = UUID("fa19dc54-a35b-4aab-adf8-816933f96fa4")
    
    # Get a real database session for tool access
    db_session_gen = get_db()
    db_session = await db_session_gen.__anext__()
    
    try:
        set_plan_tools_context(user_id=test_user_id, db_session=db_session, conversation_id=None)
        
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
    finally:
        # Always clear context and close DB session
        clear_plan_tools_context()
        await db_session.close()


def run_fitness_coach_agent_sync(**inputs) -> dict[str, Any]:
    """Synchronous wrapper for fitness coach agent."""
    import asyncio
    
    return asyncio.run(run_fitness_coach_agent(**inputs))


async def run_meal_phase_agent(**inputs) -> dict[str, Any]:
    """Run meal_phase_agent with MLflow dataset inputs.
    
    Args:
        **inputs: Keyword args containing:
            - meal_plan_description: Overall meal strategy (str)
            - phase_number: Phase number (int)
            - phase_name: Phase name (str)
            - dietary_restrictions: List of restrictions (list[str], optional)
            - meal_frequency: Meals per day (int)
    
    Returns:
        Dict with generated PhaseMealDetails (daily_calorie_target, sample_days, grocery_list, etc.)
    """
    from src.ai.app_agents.meal_phase_agent import meal_phase_agent
    
    # Build prompt for meal phase agent
    prompt = f"""Generate meal details for this phase:

Phase Context:
- Phase {inputs['phase_number']}: {inputs['phase_name']}

Overall Meal Plan:
{inputs['meal_plan_description']}

Requirements:
- Meal Frequency: {inputs['meal_frequency']} meals/day"""
    
    # Add dietary restrictions if provided
    if 'dietary_restrictions' in inputs and inputs['dietary_restrictions']:
        prompt += f"\n- Dietary Restrictions: {', '.join(inputs['dietary_restrictions'])}"
    
    prompt += "\n\nGenerate complete meal details including calorie targets, macro splits, sample days, grocery list, and prep schedules."
    
    # Run agent using Runner.run
    result = await Runner.run(
        starting_agent=meal_phase_agent,
        input=prompt,
        session=None,
    )
    
    # Extract output - should be PhaseMealDetails
    output = result.final_output
    
    # Convert to dict for MLflow (Pydantic model -> dict)
    if hasattr(output, 'model_dump'):
        output_dict = output.model_dump()
    elif hasattr(output, 'dict'):
        output_dict = output.dict()
    else:
        output_dict = output
    
    return output_dict


def run_meal_phase_agent_sync(**inputs) -> dict[str, Any]:
    """Synchronous wrapper for meal phase agent evaluation.
    
    MLflow's evaluate function expects synchronous predict functions.
    This wrapper runs the async agent using asyncio.run().
    """
    import asyncio
    
    return asyncio.run(run_meal_phase_agent(**inputs))


# ============================================================================
# Query Agent Runner
# ============================================================================

async def run_query_agent(**inputs) -> dict[str, Any]:
    """Run query_agent with MLflow dataset inputs.
    
    Args:
        **inputs: Keyword args containing:
            - user_id: User UUID (str)
            - query_request: Natural language query (str)
    
    Returns:
        Dict with agent response and query execution details
    """
    from src.ai.tools.query_tools import initialize_mcp_server, cleanup_mcp_server, _mcp_server
    
    user_id = inputs.get("user_id")
    query_request = inputs.get("query_request")
    
    # Build input with user context
    agent_input = f"""User ID: {user_id}
Query: {query_request}"""
    
    # Note: MCP server initialized once in run_query_agent_sync, not per-call
    
    # DEBUG: Verify MCP server connection
    print(f"\n[DEBUG] MCP Server initialized: {_mcp_server is not None}")
    print(f"[DEBUG] Query agent has MCP servers: {len(query_agent.mcp_servers) if query_agent.mcp_servers else 0}")
    
    if query_agent.mcp_servers:
        try:
            tools = await query_agent.mcp_servers[0].list_tools()
            tool_names = [t.name for t in tools]
            print(f"[DEBUG] Available MCP tools: {tool_names}")
            print(f"[DEBUG] 'query' tool available: {'query' in tool_names}")
        except Exception as e:
            print(f"[DEBUG] Failed to list MCP tools: {e}")
    else:
        print(f"[DEBUG] WARNING: query_agent.mcp_servers is empty!")
    
    print(f"[DEBUG] Running query agent with input: {agent_input[:100]}...\n")
    
    # Run query agent (uses postgres-mcp MCP server)
    try:
        result = await Runner.run(
            starting_agent=query_agent,
            input=agent_input,
            session=None
        )
        
        response_text = result.final_output
        
        # Extract SQL queries and results from the response if possible
        # Note: The actual SQL and results are in the MCP tool calls
        return {
            "response": response_text,
            "query_executed": True,  # Assume query executed if agent responded
            "user_id": user_id,
            "query_request": query_request,
        }
    except Exception as e:
        # Handle errors gracefully (e.g., invalid SQL, connection issues)
        error_msg = str(e)
        print(f"[ERROR] Query agent failed: {error_msg}")
        
        return {
            "response": f"Error executing query: {error_msg}",
            "query_executed": False,
            "error": True,
            "error_message": error_msg,
            "user_id": user_id,
            "query_request": query_request,
        }


# Persistent event loop and initialization flag for query_agent
import threading
_query_agent_loop: asyncio.AbstractEventLoop | None = None
_query_agent_loop_thread: threading.Thread | None = None
_query_agent_initialized = False
_query_agent_lock = threading.Lock()


def _run_event_loop_forever(loop: asyncio.AbstractEventLoop):
    """Background thread that runs the event loop forever."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def run_query_agent_sync(**inputs) -> dict[str, Any]:
    """Synchronous wrapper for run_query_agent.
    
    Uses a dedicated background thread with an event loop to keep MCP server
    alive across test cases. Worker threads submit coroutines via 
    run_coroutine_threadsafe for thread-safe concurrent execution.
    
    Handles all errors gracefully to ensure evaluation continues even when
    individual test cases fail.
    """
    import asyncio
    global _query_agent_loop, _query_agent_loop_thread, _query_agent_initialized
    
    try:
        # Initialize event loop thread once
        with _query_agent_lock:
            if _query_agent_loop is None:
                # Create new event loop for the background thread
                _query_agent_loop = asyncio.new_event_loop()
                
                # Start background thread to run the loop
                _query_agent_loop_thread = threading.Thread(
                    target=_run_event_loop_forever,
                    args=(_query_agent_loop,),
                    daemon=True,
                    name="query_agent_loop_thread"
                )
                _query_agent_loop_thread.start()
            
            # Initialize MCP server once in the background loop
            if not _query_agent_initialized:
                future = asyncio.run_coroutine_threadsafe(
                    initialize_mcp_server(),
                    _query_agent_loop
                )
                future.result(timeout=30)  # Wait for initialization
                _query_agent_initialized = True
        
        # Submit coroutine to background loop and wait for result
        future = asyncio.run_coroutine_threadsafe(
            run_query_agent(**inputs),
            _query_agent_loop
        )
        return future.result(timeout=120)  # 2 minute timeout for query execution
        
    except TimeoutError as e:
        # Timeout waiting for query to complete
        print(f"[ERROR] Query agent timeout after 120s: {inputs.get('query_request', 'unknown query')}")
        return {
            "response": f"Query timed out after 120 seconds",
            "query_executed": False,
            "error": True,
            "error_message": "Timeout waiting for query execution",
            "user_id": inputs.get("user_id"),
            "query_request": inputs.get("query_request"),
        }
    except Exception as e:
        # Catch any other errors (initialization, threading, etc.)
        error_msg = str(e)
        print(f"[ERROR] Query agent runner failed: {error_msg}")
        return {
            "response": f"System error: {error_msg}",
            "query_executed": False,
            "error": True,
            "error_message": error_msg,
            "user_id": inputs.get("user_id"),
            "query_request": inputs.get("query_request"),
        }


# ============================================================================
# Registry: Map agent names to runner functions
# ============================================================================

AGENT_RUNNERS = {
    "workout_phase_agent": run_workout_phase_agent_sync,
    "intake_agent": run_intake_agent_sync,
    "fitness_coach_agent": run_fitness_coach_agent_sync,
    "meal_phase_agent": run_meal_phase_agent_sync,
    "query_agent": run_query_agent_sync,
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
