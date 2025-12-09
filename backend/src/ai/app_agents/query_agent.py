"""Query Agent for database operations using MCP postgres-mcp server.

This agent uses OpenAI Agents SDK's MCP integration to connect to the
postgres-mcp server via stdio transport. It provides database query capabilities
to other agents without requiring direct database connections in the application.

Architecture:
    workout_plan_agent → query_agent (with MCP server) → postgres-mcp → PostgreSQL

The query agent:
- Connects to postgres-mcp via stdio (spawns subprocess)
- Accepts plain text descriptions of data needs
- Uses MCP tools provided by postgres-mcp (execute_sql, list_schemas, etc.)
- Returns formatted results

This separates database concerns from business logic and leverages
postgres-mcp's built-in safety features (read-only mode, query validation).
"""
import os

from agents import Agent
from agents.mcp import MCPServerStdio

from src.ai.agent import create_model_settings


def create_query_agent() -> Agent:
    """Create the Query Agent with postgres-mcp MCP server integration.

    This agent connects to postgres-mcp via stdio transport and automatically
    gets access to all the tools provided by the postgres-mcp server:
    - execute_sql: Execute SQL queries
    - list_schemas: List database schemas
    - list_objects: List tables/views in a schema
    - get_object_details: Get detailed table information
    - explain_query: Get query execution plans
    - analyze_db_health: Check database health
    - analyze_workload_indexes: Analyze and recommend indexes
    - get_top_queries: Get slow queries from pg_stat_statements

    The agent can use these tools to answer natural language queries about
    exercises, workouts, and other fitness data.

    Returns:
        Agent configured with postgres-mcp MCP server
    """
    # Get database URI from environment
    database_uri = os.environ.get(
        "DATABASE_URI",
        "postgresql://fitness_user:fitness_pass_dev@localhost:5432/fitness_bot"
    )

    # Create MCP server connection via stdio
    # This spawns postgres-mcp as a subprocess and communicates via stdin/stdout
    mcp_server = MCPServerStdio(
        name="postgres-mcp",
        params={
            "command": "postgres-mcp",  # Assumes postgres-mcp is in PATH (installed via uv tool)
            "args": [database_uri, "--access-mode=unrestricted"],
        },
    )

    instructions = """You are a database query specialist that helps other agents access
fitness-related data from PostgreSQL using natural language requests.

Your role is to:
1. Understand what data the requesting agent needs
2. Use the postgres-mcp MCP tools to query the database
3. Format and return results in a clear, structured way

Database Schema (public schema):
- exercises: id, name, exercise_type, target_muscle_groups (text[]),
  equipment_required (text[]), instructions, form_cues, difficulty,
  sets, reps, rest_seconds, embedding (vector(384))
- workouts: id, name, workout_details (jsonb), workout_plan_id,
  day_of_week, created_at, updated_at
- workout_plans: id, name, phase_id, created_at, updated_at
- phases: id, fitness_plan_id, objectives, start_date, end_date, created_at
- fitness_plans: id, user_id, goal_description, start_date, end_date, created_at

Available MCP Tools (from postgres-mcp):
- execute_sql: Run SELECT queries to get data
- list_schemas: List all database schemas
- list_objects: List tables/views in a schema
- get_object_details: Get columns, constraints, and indexes for a table
- explain_query: Analyze query execution plans
- analyze_db_health: Check database health metrics
- get_top_queries: Find slow queries

Query Guidelines:
- Use execute_sql for most data retrieval
- Start with SELECT queries only (read-only operations)
- Use proper SQL syntax for PostgreSQL
- Handle arrays with ANY() operator: 'chest' = ANY(target_muscle_groups)
- For vector searches: (embedding <=> '[...]'::vector) AS distance
- Return results as structured JSON when possible

Common Query Patterns:

1. Find exercises by muscle group:
   SELECT * FROM exercises WHERE 'chest' = ANY(target_muscle_groups)

2. Find exercises by equipment:
   SELECT * FROM exercises WHERE 'dumbbells' = ANY(equipment_required)

3. Find exercises by difficulty:
   SELECT * FROM exercises WHERE difficulty = 'beginner'

4. Get workout by ID:
   SELECT * FROM workouts WHERE id = 'uuid-here'

5. Semantic search (requires embedding vector):
   SELECT *, (embedding <=> '[...]'::vector) AS distance
   FROM exercises
   WHERE embedding IS NOT NULL
   ORDER BY distance LIMIT 5

IMPORTANT: When asked to do semantic/vector search, explain that you need
the embedding vector to be generated first using the sentence-transformers
model (all-MiniLM-L6-v2). The workout_plan_agent should handle embedding
generation separately if needed.

Always format your responses clearly and indicate if any limitations prevent
you from fulfilling a request (e.g., missing embedding vectors)."""

    return Agent(
        name="Query Agent",
        handoff_description="Database query specialist using postgres-mcp MCP server",
        instructions=instructions,
        model_settings=create_model_settings("balanced"),
        mcp_servers=[mcp_server],  # This gives the agent access to all postgres-mcp tools
    )


# Create singleton instance
query_agent = create_query_agent()
