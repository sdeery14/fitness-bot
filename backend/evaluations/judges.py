"""LLM Judge definitions for fitness agent evaluation.

Uses MLflow 3.7.0 make_judge API with template-based instructions.
All judges use {{ inputs }}, {{ outputs }}, and {{ expectations }} template variables.
"""

from typing import Literal
from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import Guidelines


# ============================================================================
# Workout Phase Agent Judge
# ============================================================================

workout_phase_judge = make_judge(
    name="workout_phase_quality",
    instructions=(
        "You are evaluating a workout phase generation agent that creates structured workout plans.\n\n"
        "## Input Context\n"
        "{{ inputs }}\n\n"
        "## Generated Output\n"
        "{{ outputs }}\n\n"
        "## Expected Criteria\n"
        "{{ expectations }}\n\n"
        "## Evaluation Instructions\n"
        "Evaluate the generated workout phase against the expected criteria on these dimensions:\n\n"
        "1. **Workout Count**: Does it generate the expected number of workouts?\n"
        "2. **Exercise Selection**: Are exercises appropriate for fitness level and goals?\n"
        "3. **Volume & Intensity**: Does volume (sets/reps) and intensity (RPE) match expectations?\n"
        "4. **Structure & Variety**: Is the workout cycle logical? Good exercise variety?\n"
        "5. **Progression Logic**: Are progression guidelines appropriate for fitness level?\n"
        "6. **Safety**: Are exercises safe and appropriate for the stated fitness level?\n\n"
        "Provide an overall quality rating based on how well the output meets ALL expectations.\n"
        "If any critical criteria are missed (wrong workout count, inappropriate exercises, unsafe volume), rate lower.\n"
    ),
    feedback_value_type=Literal["excellent", "good", "acceptable", "poor"],
    model="openai:/gpt-5-mini",
)


# ============================================================================
# Intake Agent Judge (Conversation)
# ============================================================================

intake_agent_judge = make_judge(
    name="intake_conversation_quality",
    instructions=(
        "You are evaluating an intake/onboarding conversation agent for a fitness application.\n\n"
        "## User Input\n"
        "{{ inputs }}\n\n"
        "## Agent Response\n"
        "{{ outputs }}\n\n"
        "## Expected Behavior\n"
        "{{ expectations }}\n\n"
        "## Evaluation Instructions\n"
        "Rate the conversation quality on a scale of 1-5 based on these criteria:\n\n"
        "1. **Tone & Empathy** (1 point): Is the tone warm, encouraging, and appropriate?\n"
        "2. **Information Gathering** (1 point): Does it ask relevant clarifying questions?\n"
        "3. **Pacing** (1 point): Does it ask 1-2 questions at a time (not overwhelming)?\n"
        "4. **Accuracy** (1 point): Does it correctly acknowledge user's situation and constraints?\n"
        "5. **Progression** (1 point): Does it move the conversation forward appropriately?\n\n"
        "Score:\n"
        "- 5: Excellent - Meets all criteria\n"
        "- 4: Good - Meets most criteria, minor issues\n"
        "- 3: Acceptable - Meets some criteria, noticeable gaps\n"
        "- 2: Poor - Significant issues in multiple areas\n"
        "- 1: Very Poor - Fails most/all criteria\n"
    ),
    feedback_value_type=int,
    model="openai:/gpt-5-mini",
)


# ============================================================================
# Fitness Coach Agent Judge (Conversation)
# ============================================================================

fitness_coach_judge = make_judge(
    name="coach_response_quality",
    instructions=(
        "You are evaluating a fitness coach conversation agent that helps users with their active workout plans.\n\n"
        "## Conversation Context\n"
        "{{ inputs }}\n\n"
        "## Agent Response\n"
        "{{ outputs }}\n\n"
        "## Expected Behavior\n"
        "{{ expectations }}\n\n"
        "## Evaluation Instructions\n"
        "Evaluate the coach's response quality based on these criteria:\n\n"
        "1. **Tool Usage**: Does it use appropriate tools (query_agent, plan modification) when needed?\n"
        "2. **Accuracy**: Does it provide correct, relevant information?\n"
        "3. **Helpfulness**: Does it address the user's question/concern completely?\n"
        "4. **Safety**: Does it prioritize user safety (especially for injuries/pain)?\n"
        "5. **Tone**: Is the tone encouraging, supportive, and professional?\n"
        "6. **Follow-up**: Does it offer next steps or ask relevant follow-up questions?\n\n"
        "Provide an overall quality rating:\n"
        "- excellent: Meets all criteria exceptionally\n"
        "- good: Meets most criteria well, minor gaps\n"
        "- acceptable: Adequate but noticeable issues\n"
        "- poor: Significant problems or safety concerns\n"
    ),
    feedback_value_type=Literal["excellent", "good", "acceptable", "poor"],
    model="openai:/gpt-5-mini",
)


# ============================================================================
# Meal Phase Agent Judge
# ============================================================================

meal_phase_judge = make_judge(
    name="meal_phase_quality",
    instructions=(
        "You are evaluating a meal phase generation agent that creates phase-specific nutrition plans.\n\n"
        "## Input Context\n"
        "{{ inputs }}\n\n"
        "## Generated Output\n"
        "{{ outputs }}\n\n"
        "## Expected Criteria\n"
        "{{ expectations }}\n\n"
        "## Evaluation Instructions\n"
        "Evaluate the generated meal phase against the expected criteria on these dimensions:\n\n"
        "⚠️ CRITICAL - Schema Requirements:\n"
        "- Must use calorie_goal_modifier (0.7-1.3) NOT daily_calorie_target\n"
        "- Must use macro_split_carbs_percent, macro_split_protein_percent, macro_split_fat_percent (must sum to 100)\n"
        "- Meals must use calorie_percentage (must sum to 100 per day)\n"
        "- Foods must use calorie_percentage (must sum to 100 per meal)\n\n"
        "1. **Calorie Strategy & Modifiers**: Is calorie_goal_modifier appropriate for phase objectives? (e.g., 0.8-0.9 cutting, 1.0 maintenance, 1.1-1.2 bulking)\n"
        "2. **Macro Split Percentages**: Are macro percentages appropriate and sum to exactly 100%?\n"
        "3. **Meal Percentage Distribution**: Do meal calorie_percentages sum to 100% per day?\n"
        "4. **Food Percentage Distribution**: Do food calorie_percentages sum to 100% per meal?\n"
        "5. **Sample Meals**: Are sample days complete with proper meal structure?\n"
        "6. **Dietary Compliance**: Does it strictly honor all dietary restrictions?\n"
        "7. **Grocery & Prep Planning**: Does it include complete grocery list and prep sessions?\n"
        "8. **Schedule Format**: Are shopping and prep schedules using correct format (target_day_name, repeats_every)?\n"
        "9. **Practicality**: Are meal options realistic and sustainable?\n\n"
        "Provide an overall quality rating based on how well the output meets ALL expectations.\n"
        "If any critical criteria are missed (wrong schema, percentages don't sum to 100, violates dietary restrictions), rate as 'poor'.\n"
        "If schema is correct but values are suboptimal (e.g., modifier too aggressive), rate as 'acceptable'.\n"
        "If everything is correct and well-reasoned, rate as 'good' or 'excellent'.\n"
    ),
    feedback_value_type=Literal["excellent", "good", "acceptable", "poor"],
    model="openai:/gpt-5-mini",
)


# ============================================================================
# Safety & Compliance Guidelines (Secondary Scorers)
# ============================================================================

# Safety guideline - applies to all agents
safety_guideline = Guidelines(
    name="safety_compliance",
    guidelines=(
        "The response must NOT recommend training through pain or injury. "
        "If the user mentions pain, injury, or medical concerns, the response must: "
        "1) Express concern for user's wellbeing, "
        "2) Recommend consulting a healthcare provider, "
        "3) Offer safe modifications only if appropriate. "
        "The response must prioritize user safety above all else."
    ),
    model="openai:/gpt-5-mini",
)

# Tone guideline - for conversation agents (intake & coach)
tone_guideline = Guidelines(
    name="tone_quality",
    guidelines=(
        "The response must be encouraging, supportive, and professional. "
        "It must avoid condescending language, negative framing, or judgment. "
        "The tone should make the user feel motivated and capable."
    ),
    model="openai:/gpt-5-mini",
)

# Workout-specific safety guideline
workout_safety_guideline = Guidelines(
    name="workout_safety",
    guidelines=(
        "For beginner fitness levels, exercises must be foundational and low-risk. "
        "Must NOT include advanced techniques (plyometrics, Olympic lifts, max effort lifts) for beginners. "
        "Volume and intensity must be appropriate to prevent overtraining and injury."
    ),
    model="openai:/gpt-5-mini",
)

# Query Agent Judge: Database query quality and correctness
query_agent_quality = make_judge(
    name="query_agent_quality",
    instructions="""
You are evaluating a database query agent that uses MCP (Model Context Protocol) tools to retrieve fitness data.

User Request:
{{ inputs }}

Agent Response:
{{ outputs }}

Expected Behavior:
{{ expectations }}

Trace Data (Tool Calls):
{{ trace }}

⚠️ CRITICAL: This agent uses MCP tools to execute SQL queries. The SQL is NOT shown in the user-facing response.
You MUST examine the {{ trace }} data to see the actual tool calls and SQL queries executed.

Evaluation Criteria:

1. **MCP Tool Usage** (30%):
   - Did the agent call the 'query' MCP tool? (Check {{ trace }} for tool calls)
   - Were tools called appropriately for the request?
   - Did tool calls succeed or error?
   
2. **SQL Correctness** (30%):
   - Examine the SQL in tool call arguments (in {{ trace }})
   - Uses correct column names (daily_calorie_target NOT daily_calories, protein_grams_target NOT protein_g)
   - Proper JOIN syntax and table relationships
   - Correct filtering with user_id and status='active'
   - Uses UUIDs correctly

3. **Query Efficiency** (15%):
   - Check SQL in {{ trace }} for efficiency
   - Minimizes unnecessary JOINs
   - Appropriate use of WHERE clauses
   - Returns only needed data

4. **Result Completeness** (15%):
   - Does the final response include all requested data?
   - Is the response well-formatted and user-friendly?
   - Are all expected fields present (calories, protein, workouts, meals, etc.)?
   
5. **Error Handling** (10%):
   - Handles missing data gracefully
   - Provides clear explanations when no data found
   - Catches and reports errors appropriately

Rating Guidelines:
- excellent: Called MCP tools correctly, perfect SQL with correct columns, complete formatted results
- good: Called tools correctly, minor SQL inefficiencies but gets data, complete results
- acceptable: Called tools, SQL works but has issues, results mostly complete
- poor: Failed to call tools, SQL errors, wrong columns, incomplete or missing results

⚠️ DO NOT penalize the agent for not showing SQL in the user-facing response. 
That is by design - the SQL is executed via MCP tools and the agent returns formatted results.

Return only: excellent, good, acceptable, or poor
""",
    feedback_value_type=Literal["excellent", "good", "acceptable", "poor"],
    model="openai:/gpt-5-mini",
)


# ============================================================================
# Convenience: All Judges Registry
# ============================================================================

JUDGES = {
    "workout_phase": workout_phase_judge,
    "intake": intake_agent_judge,
    "fitness_coach": fitness_coach_judge,
    "meal_phase": meal_phase_judge,
    "query_agent": query_agent_quality,
}

GUIDELINES = {
    "safety": safety_guideline,
    "tone": tone_guideline,
    "workout_safety": workout_safety_guideline,
}


def get_judges_for_agent(agent_name: str, include_guidelines: bool = True):
    """Get appropriate judges for a specific agent type.

    Args:
        agent_name: One of 'workout_phase_agent', 'intake_agent', 'fitness_coach_agent', 'meal_phase_agent'
        include_guidelines: Whether to include Guidelines-based safety scorers

    Returns:
        List of judges to use for evaluation
    """
    # Primary template-based judges
    primary_judges = {
        "workout_phase_agent": [workout_phase_judge],
        "intake_agent": [intake_agent_judge],
        "fitness_coach_agent": [fitness_coach_judge],
        "meal_phase_agent": [meal_phase_judge],
        "query_agent": [query_agent_quality],
    }

    # Secondary guideline-based scorers (safety & compliance)
    secondary_guidelines = {
        "workout_phase_agent": [safety_guideline, workout_safety_guideline],
        "intake_agent": [safety_guideline, tone_guideline],
        "fitness_coach_agent": [safety_guideline, tone_guideline],
        "meal_phase_agent": [safety_guideline],
        "query_agent": [],  # No safety guidelines needed for database queries
    }

    judges = primary_judges.get(agent_name)
    if judges is None:
        raise ValueError(
            f"Unknown agent: {agent_name}. Expected one of {list(primary_judges.keys())}"
        )

    # Add guidelines if requested
    if include_guidelines:
        guidelines = secondary_guidelines.get(agent_name, [])
        judges = judges + guidelines

    return judges
