"""Meal planning tools using USDA FoodData Central API.

These tools wrap the USDA API client for use by AI agents.
All tools return JSON strings as required by OpenAI Agents SDK.
"""
import json

from agents import function_tool

from src.integrations.usda_fooddata import usda_client


@function_tool
async def search_usda_foods(
    query: str,
    data_type: str | None = None,
) -> str:
    """Search USDA FoodData Central for foods.

    Args:
        query: Search query (e.g., "chicken breast", "brown rice")
        data_type: Optional filter - one of: Foundation, SR Legacy, Survey, Branded

    Returns:
        JSON string with search results including FDC IDs and descriptions
    """
    data_types = [data_type] if data_type else None
    results = await usda_client.search_foods(query, data_types)
    return json.dumps(results, indent=2)


@function_tool
async def get_food_nutrition(fdc_id: int) -> str:
    """Get detailed nutritional information for a specific food.

    Args:
        fdc_id: FoodData Central ID from search results

    Returns:
        JSON string with complete nutritional data including macros and micros
    """
    details = await usda_client.get_food_details(fdc_id)
    return json.dumps(details, indent=2)


@function_tool
async def calculate_meal_macros(
    fdc_id: int,
    amount: float,
    unit: str = "g",
) -> str:
    """Calculate macronutrients for a specific portion of food.

    Args:
        fdc_id: FoodData Central ID
        amount: Quantity of food
        unit: Unit of measurement (g, oz, cup, etc.) - default is grams

    Returns:
        JSON string with calories, protein, carbs, fat for the specified portion
    """
    macros = await usda_client.calculate_portions(fdc_id, amount, unit)
    return json.dumps(macros, indent=2)
