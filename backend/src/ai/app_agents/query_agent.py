"""Query Agent for database operations using MCP postgres-mcp server.

This agent uses OpenAI Agents SDK's MCP integration to connect to the
postgres-mcp server via stdio transport. It provides database query capabilities
to other agents without requiring direct database connections in the application.

Architecture:
    workout_plan_agent → query_agent (with MCP server) → postgres-mcp → PostgreSQL

The query agent:
- MCP server is initialized lazily in query_tools.py to avoid async context issues
- Accepts plain text descriptions of data needs
- Uses MCP tools provided by postgres-mcp (execute_sql, list_schemas, etc.)
- Returns formatted results

This separates database concerns from business logic and leverages
postgres-mcp's built-in safety features (read-only mode, query validation).
"""
from agents import Agent

from src.ai.agent import create_model_settings


def create_query_agent() -> Agent:
    """Create the Query Agent for database operations.

    This agent is designed to work with the postgres-mcp MCP server that gets
    initialized lazily by query_tools.py when the query_database function is called.
    The MCP server connection is added to this agent dynamically at runtime.

    The agent gets access to all the tools provided by the postgres-mcp server:
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
        Agent configured for database queries (MCP server added at runtime)
    """
    # Note: MCP server is NOT created here to avoid async context issues
    # It's created lazily in query_tools.py when first needed

    instructions = """You are a database query specialist that helps other agents access
fitness-related data from PostgreSQL using natural language requests.

Your role is to:
1. Understand what data the requesting agent needs
2. Use the postgres-mcp MCP tools to query the database
3. Format and return results in a clear, structured way

Database Schema (public schema):

Key Tables:
- exercise_catalog: CURATED exercise database (28 exercises, pre-seeded)
  * id, name, exercise_type, target_muscle_groups (json), equipment_required (json),
    difficulty (beginner/intermediate/advanced), instructions, form_cues (json),
    alternatives (json), embedding (vector(384))
  * Use this for finding exercises to include in new workout plans
  * Query by difficulty, equipment, muscle groups, or semantic search

- fitness_plans: id, user_id, goal_type, goal_description, target_weight_kg,
  target_date, duration_weeks, start_date, end_date, status, plan_snapshot (json)

- phases: id, fitness_plan_id, phase_number, name, objectives (json),
  start_date, end_date, phase_details (json)

- workout_plans: id, fitness_plan_id, frequency_per_week, progression_strategy,
  workout_plan_details (json)

- workouts: id, workout_plan_id, phase_id, name, workout_type, duration_minutes,
  intensity_level, workout_structure (json)

- exercises: id, workout_id, exercise_order, name, exercise_type,
  target_muscle_groups (json), equipment_required (json), sets, reps,
  duration_seconds, rest_seconds, tempo, rpe_target, instructions,
  form_cues (json), alternative_exercise_ids (json), embedding (vector(384))
  * User-specific exercise instances within workouts (NOT the catalog)

- meal_plans: id, fitness_plan_id, daily_calories, protein_g, carbs_g,
  fat_g, meal_plan_details (json)

- meals: id, meal_plan_id, phase_id, meal_type, name, calories, protein_g,
  carbs_g, fat_g, ingredients (json), preparation_instructions

- users: id, email, full_name, current_fitness_level, preferences (json), timezone

- schedules: id, user_id, fitness_plan_id, split_type, schedule_config (json)

- schedule_entries: id, schedule_id, workout_id, scheduled_date, scheduled_time,
  status, completion_time

Available MCP Tools (from postgres-mcp):
- execute_sql: Run SELECT queries to get data
- list_schemas: List all database schemas
- list_objects: List tables/views in a schema
- get_object_details: Get columns, constraints, and indexes for a table
- explain_query: Analyze query execution plans
- analyze_db_health: Check database health metrics
- get_top_queries: Find slow queries from pg_stat_statements

Query Guidelines:
- Use execute_sql for most data retrieval
- Start with SELECT queries only (read-only operations)
- Use proper SQL syntax for PostgreSQL
- JSON columns use json type, access with -> or ->> operators
- For vector searches: (embedding <=> '[...]'::vector) AS distance
- Return results as structured JSON when possible
- All IDs are UUIDs

Common Query Examples:

1. **Find exercises from CATALOG** (use when building new plans):
   SELECT name, exercise_type, difficulty, target_muscle_groups, equipment_required
   FROM exercise_catalog
   WHERE difficulty = 'beginner'
   AND equipment_required::text LIKE '%bodyweight%'

2. **Find exercises by muscle group from CATALOG**:
   SELECT name, exercise_type, instructions, form_cues
   FROM exercise_catalog
   WHERE target_muscle_groups::text LIKE '%chest%'

3. **Semantic search for similar exercises in CATALOG**:
   SELECT name, exercise_type, (embedding <=> '[...]'::vector) AS distance
   FROM exercise_catalog
   WHERE embedding IS NOT NULL
   ORDER BY distance LIMIT 10

4. **Get exercises for a specific user workout**:
   SELECT * FROM exercises WHERE workout_id = 'uuid-here' ORDER BY exercise_order

5. **Get all workouts in a phase**:
   SELECT * FROM workouts WHERE phase_id = 'uuid-here'

6. **Get user's active fitness plan**:
   SELECT * FROM fitness_plans WHERE user_id = 'uuid-here' AND status = 'active'

7. **Get workout plan details**:
   SELECT wp.*, fp.goal_type, fp.duration_weeks
   FROM workout_plans wp
   JOIN fitness_plans fp ON wp.fitness_plan_id = fp.id
   WHERE fp.user_id = 'uuid-here'

CRITICAL DISTINCTIONS:
- **exercise_catalog**: 28 pre-seeded curated exercises for building NEW plans
  * Query this when agents need to FIND exercises to include in plans
  * Has "difficulty" column (beginner/intermediate/advanced)
  * Independent of any user or workout

- **exercises**: User-specific exercise instances within actual workouts
  * Query this when viewing EXISTING workout details
  * Linked to workouts via workout_id foreign key
  * Created when plans are generated, not pre-seeded

JSON column queries:
- Use ::text for LIKE searches: target_muscle_groups::text LIKE '%chest%'
- Use -> for json access: target_muscle_groups->'0' for first element
- Always use proper UUID format for ID queries

Always format your responses clearly and indicate if any limitations prevent
you from fulfilling a request."""

    return Agent(
        name="Query Agent",
        handoff_description="Database query specialist using postgres-mcp MCP server",
        instructions=instructions,
        model_settings=create_model_settings(),
        # MCP server is added dynamically by query_tools.py at runtime
    )


# Create singleton instance
query_agent = create_query_agent()
