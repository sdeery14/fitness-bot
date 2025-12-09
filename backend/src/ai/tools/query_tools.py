"""Function tools for querying the database via MCP postgres-mcp server.

These tools wrap the MCP query agent, allowing other agents (like workout_plan_agent)
to query the database using natural language descriptions that get translated to SQL.

Architecture:
    workout_plan_agent → query_database → query_agent (with MCP server) → PostgreSQL
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


async def cleanup_mcp_server():
    """Clean up the MCP server connection.

    Should be called when the application shuts down.
    """
    server = _mcp_server_context.get()
    if server is not None:
        await server.__aexit__(None, None, None)
        _mcp_server_context.set(None)
