"""Query Agent for database operations using MCP postgres-mcp server.

This agent uses OpenAI Agents SDK's MCP integration to connect to the
postgres-mcp server via stdio transport. It provides database query capabilities
to other agents without requiring direct database connections in the application.

Architecture:
    workout_phase_agent → query_agent (with MCP server) → postgres-mcp → PostgreSQL

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

Key Tables (ACCURATE SCHEMA - USE THESE EXACT COLUMN NAMES):

- fitness_plans: User's fitness plans
  Columns: id (uuid), user_id (uuid), goal_type (varchar), goal_description (text),
  target_weight_kg (varchar), target_date (timestamptz), duration_weeks (int),
  start_date (timestamptz), end_date (timestamptz), status (enum),
  parent_plan_id (uuid), version (int), version_notes (text),
  key_principles (json), success_metrics (json), important_notes (text),
  created_at (timestamptz), updated_at (timestamptz)
  
  * Plan data stored in normalized tables: phases, workout_plans, workouts, exercises, meal_plans, meals
  * status can be: 'draft', 'active', 'paused', 'completed', 'abandoned', 'replaced'
  * parent_plan_id links to previous version of plan (for plan versioning)
  * key_principles: Core principles guiding the plan (array of strings)
  * success_metrics: How to measure success (array of strings)
  * important_notes: Critical information and warnings

- phases: Training phases within a fitness plan
  Columns: id (uuid), fitness_plan_id (uuid), phase_number (int), name (varchar),
  objectives (json), start_date (timestamptz), end_date (timestamptz),
  phase_details (json), created_at (timestamptz), updated_at (timestamptz)

- workout_plans: Workout plan metadata
  Columns: id (uuid), fitness_plan_id (uuid), frequency_per_week (int),
  progression_strategy (varchar), workout_plan_details (json),
  phase_progression_notes (text), equipment_used (json),
  created_at (timestamptz), updated_at (timestamptz)
  
  * phase_progression_notes: How phases progress in intensity/volume
  * equipment_used: Required equipment (array of strings)

- meal_plans: Meal plan metadata
  Columns: id (uuid), fitness_plan_id (uuid), daily_calorie_target (int),
  macronutrient_distribution (json), protein_grams_target (int),
  carbs_grams_target (int), fats_grams_target (int), meals_per_day (int),
  dietary_approach (varchar), macro_strategy (varchar), meal_timing (varchar),
  hydration_guidance (varchar), phase_nutrition_notes (varchar),
  created_at (timestamptz), updated_at (timestamptz)
  
  ⚠️ CRITICAL: Use these EXACT column names:
  - daily_calorie_target (NOT daily_calories)
  - protein_grams_target (NOT protein_g)
  - carbs_grams_target (NOT carbs_g)
  - fats_grams_target (NOT fat_g)
  
  * dietary_approach: Diet philosophy/approach
  * macro_strategy: Macro distribution strategy
  * meal_timing: Meal timing guidance
  * hydration_guidance: Water intake guidelines
  * phase_nutrition_notes: How nutrition changes across phases

- workouts: Individual workout sessions
  Columns: id (uuid), workout_plan_id (uuid), phase_id (uuid), name (varchar),
  workout_type (varchar), duration_minutes (int), intensity_level (varchar),
  workout_structure (json), created_at (timestamptz), updated_at (timestamptz)

- exercises: Exercise instances within workouts
  Columns: id (uuid), workout_id (uuid), exercise_order (int), name (varchar),
  exercise_type (varchar), target_muscle_groups (json), equipment_required (json),
  sets (int), reps (varchar), duration_seconds (int), rest_seconds (int),
  tempo (varchar), rpe_target (int), instructions (text), form_cues (json),
  alternative_exercise_ids (json), embedding (vector(384)),
  created_at (timestamptz), updated_at (timestamptz)

- meals: Individual meals
  Columns: id (uuid), meal_plan_id (uuid), phase_id (uuid), meal_type (varchar),
  name (varchar), calories (int), protein_g (int), carbs_g (int), fat_g (int),
  ingredients (json), preparation_instructions (text),
  created_at (timestamptz), updated_at (timestamptz)

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

Common Query Examples (USE EXACT COLUMN NAMES):

1. **Get user's active fitness plan with all data**:
   SELECT fp.*, ph.phase_number, ph.name AS phase_name, ph.objectives,
          wp.frequency_per_week, wp.progression_strategy,
          mp.daily_calorie_target, mp.protein_grams_target, 
          mp.carbs_grams_target, mp.fats_grams_target
   FROM fitness_plans fp
   LEFT JOIN phases ph ON fp.id = ph.fitness_plan_id
   LEFT JOIN workout_plans wp ON fp.id = wp.fitness_plan_id
   LEFT JOIN meal_plans mp ON fp.id = mp.fitness_plan_id
   WHERE fp.user_id = 'uuid-here' AND fp.status = 'active'

2. **Get specific phase details**:
   SELECT * FROM phases 
   WHERE fitness_plan_id = 'uuid-here' 
   ORDER BY phase_number

3. **Get workout plan details**:
   SELECT wp.*, fp.goal_type, fp.duration_weeks
   FROM workout_plans wp
   JOIN fitness_plans fp ON wp.fitness_plan_id = fp.id
   WHERE fp.user_id = 'uuid-here'

4. **Get meal plan with correct column names**:
   SELECT mp.daily_calorie_target, mp.protein_grams_target,
          mp.carbs_grams_target, mp.fats_grams_target, mp.meals_per_day
   FROM meal_plans mp
   JOIN fitness_plans fp ON mp.fitness_plan_id = fp.id
   WHERE fp.user_id = 'uuid-here' AND fp.status = 'active'

5. **Get all workouts in a phase**:
   SELECT * FROM workouts WHERE phase_id = 'uuid-here'

7. **Get exercises for a workout**:
   SELECT * FROM exercises 
   WHERE workout_id = 'uuid-here' 
   ORDER BY exercise_order

CRITICAL REMINDERS:
⚠️ meal_plans columns:
  - daily_calorie_target (NOT daily_calories)
  - protein_grams_target (NOT protein_g)
  - carbs_grams_target (NOT carbs_g)
  - fats_grams_target (NOT fat_g)

⚠️ All timestamps are timestamptz (with timezone)
⚠️ All IDs are uuid type
⚠️ Use ::text for LIKE searches on JSON: objectives::text LIKE '%strength%'

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
