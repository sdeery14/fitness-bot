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


@function_tool
def suggest_variations(
    meal_id: str,
    dietary_preference: str = None,
    calorie_target: int = None,
) -> str:
    """Suggest meal variations based on dietary preferences or calorie targets.

    Args:
        meal_id: UUID of the meal to create variations for
        dietary_preference: Optional preference (vegetarian, vegan, low-carb, high-protein, etc.)
        calorie_target: Optional target calories to match

    Returns:
        JSON string with suggested meal variations
    """
    import asyncio
    from uuid import UUID

    from sqlalchemy import select

    from src.database import AsyncSessionLocal
    from src.models.meal import Meal

    async def _get_variations():
        async with AsyncSessionLocal() as db:
            stmt = select(Meal).where(Meal.id == UUID(meal_id))
            result = await db.execute(stmt)
            meal = result.scalar_one_or_none()

            if not meal:
                return {"error": f"Meal {meal_id} not found"}

            variations = []

            # Create variations based on dietary preference
            if dietary_preference:
                if dietary_preference.lower() in ["vegetarian", "vegan"]:
                    vegetarian_swap = {
                        "variation_name": f"{meal.name} ({dietary_preference.title()})",
                        "changes": [
                            {"from": "chicken", "to": "tofu", "reason": "Plant-based protein"},
                            {"from": "beef", "to": "black beans", "reason": "Plant-based protein"},
                            {"from": "fish", "to": "tempeh", "reason": "Plant-based protein"},
                        ],
                        "estimated_calories": meal.calories,
                        "estimated_protein": max(20, meal.protein_grams - 5),
                    }
                    variations.append(vegetarian_swap)

                elif dietary_preference.lower() == "low-carb":
                    low_carb_swap = {
                        "variation_name": f"{meal.name} (Low-Carb)",
                        "changes": [
                            {"from": "rice", "to": "cauliflower rice", "reason": "Lower carbs"},
                            {"from": "pasta", "to": "zucchini noodles", "reason": "Lower carbs"},
                            {"from": "bread", "to": "lettuce wrap", "reason": "Lower carbs"},
                        ],
                        "estimated_calories": max(200, meal.calories - 150),
                        "estimated_carbs": max(10, meal.carbs_grams - 30),
                    }
                    variations.append(low_carb_swap)

                elif dietary_preference.lower() == "high-protein":
                    high_protein_swap = {
                        "variation_name": f"{meal.name} (High-Protein)",
                        "changes": [
                            {"add": "protein powder", "amount": "1 scoop", "reason": "+25g protein"},
                            {"add": "egg whites", "amount": "100g", "reason": "+11g protein"},
                            {"increase": "chicken breast", "by": "50g", "reason": "+15g protein"},
                        ],
                        "estimated_calories": meal.calories + 100,
                        "estimated_protein": meal.protein_grams + 25,
                    }
                    variations.append(high_protein_swap)

            # Create calorie-adjusted variation
            if calorie_target:
                calorie_diff = calorie_target - meal.calories
                adjustment_type = "increase" if calorie_diff > 0 else "decrease"
                percentage = abs(calorie_diff / meal.calories * 100)

                calorie_adjusted = {
                    "variation_name": f"{meal.name} ({calorie_target} cal)",
                    "adjustment": f"{adjustment_type.title()} portions by {percentage:.0f}%",
                    "changes": [
                        {"action": "adjust_all_portions", "percentage": percentage, "direction": adjustment_type}
                    ],
                    "target_calories": calorie_target,
                }
                variations.append(calorie_adjusted)

            return {
                "meal_id": meal_id,
                "original_meal": meal.name,
                "original_calories": meal.calories,
                "original_protein": meal.protein_grams,
                "original_carbs": meal.carbs_grams,
                "original_fat": meal.fat_grams,
                "variations": variations,
                "recommendation": f"Found {len(variations)} variations based on your preferences",
            }

    result = asyncio.run(_get_variations())
    return json.dumps(result, indent=2)


@function_tool
def update_macros(
    meal_id: str,
    target_protein: int = None,
    target_carbs: int = None,
    target_fat: int = None,
) -> str:
    """Update meal to hit specific macro targets.

    Args:
        meal_id: UUID of the meal to modify
        target_protein: Target protein in grams
        target_carbs: Target carbs in grams
        target_fat: Target fat in grams

    Returns:
        JSON string with suggested ingredient adjustments to meet macro targets
    """
    import asyncio
    from uuid import UUID

    from sqlalchemy import select

    from src.database import AsyncSessionLocal
    from src.models.meal import Meal

    async def _update():
        async with AsyncSessionLocal() as db:
            stmt = select(Meal).where(Meal.id == UUID(meal_id))
            result = await db.execute(stmt)
            meal = result.scalar_one_or_none()

            if not meal:
                return {"error": f"Meal {meal_id} not found"}

            adjustments = []

            if target_protein and target_protein != meal.protein_grams:
                protein_diff = target_protein - meal.protein_grams
                adjustments.append({
                    "macro": "protein",
                    "current": meal.protein_grams,
                    "target": target_protein,
                    "difference": protein_diff,
                    "suggestion": f"{'Add' if protein_diff > 0 else 'Reduce'} protein source by ~{abs(protein_diff)}g"
                    + (" (e.g., +100g chicken breast)" if protein_diff > 0 else ""),
                })

            if target_carbs and target_carbs != meal.carbs_grams:
                carbs_diff = target_carbs - meal.carbs_grams
                adjustments.append({
                    "macro": "carbs",
                    "current": meal.carbs_grams,
                    "target": target_carbs,
                    "difference": carbs_diff,
                    "suggestion": f"{'Add' if carbs_diff > 0 else 'Reduce'} carb source by ~{abs(carbs_diff)}g"
                    + (" (e.g., +50g rice)" if carbs_diff > 0 else ""),
                })

            if target_fat and target_fat != meal.fat_grams:
                fat_diff = target_fat - meal.fat_grams
                adjustments.append({
                    "macro": "fat",
                    "current": meal.fat_grams,
                    "target": target_fat,
                    "difference": fat_diff,
                    "suggestion": f"{'Add' if fat_diff > 0 else 'Reduce'} fat source by ~{abs(fat_diff)}g"
                    + (" (e.g., +1 tbsp olive oil)" if fat_diff > 0 else ""),
                })

            new_calories = (
                (target_protein or meal.protein_grams) * 4
                + (target_carbs or meal.carbs_grams) * 4
                + (target_fat or meal.fat_grams) * 9
            )

            return {
                "meal_id": meal_id,
                "meal_name": meal.name,
                "original_macros": {
                    "protein": meal.protein_grams,
                    "carbs": meal.carbs_grams,
                    "fat": meal.fat_grams,
                    "calories": meal.calories,
                },
                "target_macros": {
                    "protein": target_protein or meal.protein_grams,
                    "carbs": target_carbs or meal.carbs_grams,
                    "fat": target_fat or meal.fat_grams,
                    "estimated_calories": new_calories,
                },
                "adjustments": adjustments,
                "notes": "Adjust ingredient portions to meet macro targets",
            }

    result = asyncio.run(_update())
    return json.dumps(result, indent=2)


@function_tool
def swap_ingredients(
    meal_id: str,
    ingredient_to_replace: str,
    reason: str,
) -> str:
    """Suggest ingredient swaps for a meal.

    Args:
        meal_id: UUID of the meal
        ingredient_to_replace: Name of ingredient to swap out
        reason: Reason for swap (allergy, preference, availability, cost)

    Returns:
        JSON string with suggested ingredient replacements
    """
    import asyncio
    from uuid import UUID

    from sqlalchemy import select

    from src.database import AsyncSessionLocal
    from src.models.meal import Meal

    async def _swap():
        async with AsyncSessionLocal() as db:
            stmt = select(Meal).where(Meal.id == UUID(meal_id))
            result = await db.execute(stmt)
            meal = result.scalar_one_or_none()

            if not meal:
                return {"error": f"Meal {meal_id} not found"}

            # Common ingredient swaps based on reason
            swap_suggestions = {
                "chicken": {
                    "allergy": ["turkey", "tofu", "tempeh"],
                    "preference": ["turkey", "lean beef", "fish"],
                    "availability": ["canned chicken", "ground turkey"],
                    "cost": ["eggs", "canned tuna", "chicken thighs"],
                },
                "rice": {
                    "allergy": ["quinoa", "cauliflower rice"],
                    "preference": ["pasta", "couscous", "farro"],
                    "availability": ["pasta", "potatoes"],
                    "cost": ["pasta", "oats"],
                },
                "milk": {
                    "allergy": ["almond milk", "oat milk", "soy milk"],
                    "preference": ["almond milk", "coconut milk"],
                    "availability": ["water + protein powder"],
                    "cost": ["water", "powdered milk"],
                },
            }

            ingredient_lower = ingredient_to_replace.lower()
            reason_lower = reason.lower()

            # Find matching swaps
            suggestions = []
            for key, swaps in swap_suggestions.items():
                if key in ingredient_lower:
                    if reason_lower in swaps:
                        suggestions = swaps[reason_lower]
                    else:
                        # Default to preference swaps
                        suggestions = swaps.get("preference", [])
                    break

            # If no predefined swaps, provide general guidance
            if not suggestions:
                suggestions = [f"Similar protein source to {ingredient_to_replace}"]

            return {
                "meal_id": meal_id,
                "meal_name": meal.name,
                "ingredient_to_replace": ingredient_to_replace,
                "reason": reason,
                "suggested_swaps": suggestions,
                "notes": "Adjust quantities to maintain similar macros",
            }

    result = asyncio.run(_swap())
    return json.dumps(result, indent=2)

