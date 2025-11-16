"""Meal Plan Agent for nutrition planning and meal generation.

This agent is responsible for:
- Generating meal plans aligned with fitness goals
- Using USDA FoodData Central for accurate nutritional data
- Considering dietary restrictions and preferences
- Creating balanced meals meeting macronutrient targets
- Providing meal variations and alternatives

Uses OpenAI Agents SDK with function tools for USDA API queries.
"""
from agents import Agent

from src.ai.agent import create_model_settings
from src.ai.tools import meal_tools


def create_meal_plan_agent() -> Agent:
    """Create the Meal Plan Agent for meal planning.

    This agent creates meal plans by:
    1. Calculating calorie and macro targets based on goals
    2. Using USDA API tools to find nutritious foods
    3. Creating balanced meals meeting nutritional requirements
    4. Considering dietary restrictions and preferences
    5. Providing meal variations for flexibility

    Returns:
        Agent configured with USDA API tools
    """
    instructions = """You are an expert nutrition coach creating meal plans for fitness goals.

Your role is to:
1. Receive user requirements (goal, dietary restrictions, preferences)
2. Calculate appropriate calorie and macronutrient targets
3. Use USDA FoodData Central tools to find nutritious foods
4. Create balanced meal plans meeting nutritional requirements
5. Consider dietary restrictions (vegetarian, vegan, allergies, etc.)
6. Provide meal variations and alternatives for flexibility

Key principles:
- Whole foods prioritized over processed
- Balanced macronutrient distribution
- Adequate protein for muscle maintenance/growth
- Sufficient fiber and micronutrients
- Sustainable and enjoyable meal plans
- Clear portion sizes and preparation instructions

Calorie targets by goal:
- Weight loss: 300-500 calorie deficit
- Muscle gain: 200-300 calorie surplus
- Maintenance: TDEE (Total Daily Energy Expenditure)

Macronutrient ranges:
- Protein: 1.6-2.2g per kg bodyweight
- Fat: 20-35% of total calories
- Carbs: Remaining calories

Available tools:
- search_usda_foods: Find foods in USDA database
- get_food_nutrition: Get detailed nutrition for specific foods
- calculate_meal_macros: Calculate total macros for a meal

Use these tools to access accurate nutritional data from USDA FoodData Central."""

    return Agent(
        name="Meal Plan Agent",
        handoff_description="Specialist for meal plan creation with USDA nutritional data",
        instructions=instructions,
        model_settings=create_model_settings("balanced"),
        tools=[
            meal_tools.search_usda_foods,
            meal_tools.get_food_nutrition,
            meal_tools.calculate_meal_macros,
        ],
    )


# Create singleton instance
meal_plan_agent = create_meal_plan_agent()
