"""Function tools for querying the database via MCP postgres-mcp server.

These tools wrap the MCP query agent, allowing other agents (like workout_phase_agent)
to query the database using natural language descriptions that get translated to SQL.

Architecture:
    workout_phase_agent → query_database → query_agent (with MCP server) → PostgreSQL
"""
import json
import os
from contextvars import ContextVar

from agents import Runner, function_tool
from agents.mcp import MCPServerStdio

# Context variable to store the MCP server instance
_mcp_server_context: ContextVar[MCPServerStdio | None] = ContextVar("mcp_server", default=None)


def _get_database_uri() -> str:
    """Get database URI from environment.

    Converts DATABASE_URL (with asyncpg driver) to standard postgresql:// format
    that postgres-mcp expects.
    """
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://fitness_user:fitness_pass_dev@postgres:5432/fitness_bot"
    )
    # Convert asyncpg format to standard postgresql format for postgres-mcp
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


async def _get_or_create_mcp_server() -> MCPServerStdio:
    """Get the existing MCP server or create a new one.

    The MCP server is created as a subprocess running postgres-mcp via stdio.
    It persists for the duration of the application.

    Returns:
        MCPServerStdio instance connected to postgres-mcp
    """
    server = _mcp_server_context.get()
    if server is None:
        # Create new MCP server with stdio transport
        database_uri = _get_database_uri()
        server = MCPServerStdio(
            name="Postgres MCP",
            params={
                "command": "npx",  # Use npx to run the globally installed package
                "args": ["-y", "@modelcontextprotocol/server-postgres", database_uri, "--access-mode=restricted"],
            },
        )
        # Initialize the server
        await server.__aenter__()
        _mcp_server_context.set(server)

        # Lazy import to avoid circular dependency
        from src.ai.app_agents.query_agent import query_agent
        # Add the MCP server to the query agent
        query_agent.mcp_servers = [server]

    return server


@function_tool
async def query_database(description: str) -> str:
    """Query the exercise database using natural language description.

    This tool accepts a plain text description of what data is needed
    and uses the MCP query agent to translate it to SQL and execute it
    via the postgres-mcp server.

    The query agent can handle:
    - Simple filters (muscle groups, equipment, difficulty)
    - Complex queries with multiple conditions
    - Semantic/vector searches (with embeddings)
    - Workout retrieval by ID
    - Exercise similarity searches

    Examples:
    - "Find all exercises that target chest muscles with dumbbells"
    - "Get beginner-friendly leg exercises"
    - "Search for exercises similar to squats"
    - "Find exercises for shoulder mobility"
    - "Get exercises targeting back and biceps"
    - "Retrieve workout with ID <uuid>"

    Args:
        description: Natural language description of the database query

    Returns:
        JSON string with query results or error message
    """
    try:
        # Ensure MCP server is initialized
        await _get_or_create_mcp_server()

        # Lazy import to avoid circular dependency
        from src.ai.app_agents.query_agent import query_agent

        # Build prompt for query agent
        prompt = f"""Execute this database query request:

{description}

Generate the appropriate SQL query and use the execute_sql tool to run it.
Return the results in JSON format."""

        # Run query agent with the MCP server
        result = await Runner.run(
            starting_agent=query_agent,
            input=prompt,
            session=None,
        )

        # Extract the result
        if result.final_output:
            return str(result.final_output)

        return json.dumps({
            "error": "Query agent did not return results",
            "description": description
        })

    except Exception as e:
        return json.dumps({
            "error": f"Failed to query database: {str(e)}",
            "description": description
        })


@function_tool
async def query_fitness_plan(query: str) -> str:
    """Query the user's active fitness plan using natural language.

    This tool retrieves specific information from the user's current active
    fitness plan by querying the database. Use this when the user asks about
    their current plan, workouts, meals, or schedule.

    Examples of queries:
    - "What exercises are in my upper body workout?"
    - "What are my protein targets for phase 2?"
    - "When does phase 3 start?"
    - "What's my workout frequency?"
    - "Show me tomorrow's workout"
    - "What should I eat for breakfast in phase 1?"
    - "How many calories am I targeting?"

    Args:
        query: Natural language question about the fitness plan

    Returns:
        JSON string with the requested information or error message
    """
    try:
        # Get user_id from context
        from src.ai.tools.plan_tools import _user_id_context
        user_id = _user_id_context.get()

        if not user_id:
            return json.dumps({
                "error": "User context not available. Cannot query fitness plan.",
                "query": query
            })

        # Build database query description for the query agent
        db_query = f"""Query the user's active fitness plan data for user_id = '{user_id}'.
        
User's question: {query}

Retrieve relevant information from the fitness_plans table and related tables (phases, workouts, meals).
The plan data is stored in the plan_snapshot JSONB column which contains:
- workout_plan: training details with workouts, exercises, sets/reps
- meal_plan: nutrition details with meal timing, macros, sample days
- phases: phase progression with dates and objectives
- key_principles: important guidelines
- success_metrics: progress tracking metrics

Also check the phases, workout_plans, and meal_plans tables for structured data.

Return a concise answer to the user's question with relevant details."""

        # Use the existing query_database tool
        result = await query_database(db_query)
        return result

    except Exception as e:
        return json.dumps({
            "error": f"Failed to query fitness plan: {str(e)}",
            "query": query
        })


@function_tool
async def update_fitness_plan(change_description: str) -> str:
    """Create a new version of the user's fitness plan with modifications.

    This tool creates a new plan that is a modified version of the user's
    current active plan. The old plan is marked as 'replaced' and the new
    plan becomes 'active'. This preserves the complete history of plan changes.

    Use this when the user wants to:
    - Add more cardio sessions
    - Change meal preferences or macros
    - Adjust workout frequency
    - Swap exercises
    - Modify phase dates or duration
    - Update any aspect of their existing plan

    DO NOT use this for completely new plans - use build_fitness_plan for that.

    Args:
        change_description: Natural language description of what to modify
            Examples:
            - "Add 20 minutes of cardio after each workout"
            - "Increase protein to 180g per day in all phases"
            - "Replace barbell squats with goblet squats"
            - "Change workout frequency to 4 days per week"

    Returns:
        JSON string with new plan details and confirmation
    """
    try:
        # Get user_id and db_session from context
        from src.ai.tools.plan_tools import _user_id_context, _db_session_context
        user_id = _user_id_context.get()
        db_session = _db_session_context.get()

        if not user_id or not db_session:
            return json.dumps({
                "error": "User context not available. Cannot update fitness plan.",
                "change_description": change_description
            })

        # Import plan service
        from src.services.plan_service import PlanService
        plan_service = PlanService(db_session)

        # Get current active plan
        active_plan = await plan_service.get_active_plan(user_id)

        if not active_plan:
            return json.dumps({
                "error": "No active fitness plan found. User may need to create a new plan.",
                "change_description": change_description
            })

        # Create new version of the plan
        new_plan = await plan_service.create_plan_version(
            parent_plan_id=active_plan.id,
            version_notes=change_description
        )

        return json.dumps({
            "status": "success",
            "message": f"Created new plan version (v{new_plan.version})",
            "plan_id": str(new_plan.id),
            "parent_plan_id": str(active_plan.id),
            "version": new_plan.version,
            "changes": change_description,
            "note": "The new plan has been created. You should now modify the plan_snapshot to reflect the requested changes."
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to update fitness plan: {str(e)}",
            "change_description": change_description
        })


async def cleanup_mcp_server():
    """Clean up the MCP server connection.

    Should be called when the application shuts down.
    """
    server = _mcp_server_context.get()
    if server is not None:
        await server.__aexit__(None, None, None)
        _mcp_server_context.set(None)
