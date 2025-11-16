"""USDA FoodData Central API client for nutritional data."""
import asyncio
from typing import Any, Optional

import httpx

from src.config import settings


class USDAFoodDataClient:
    """Client for USDA FoodData Central API."""

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize USDA API client.
        
        Args:
            api_key: USDA API key. If not provided, uses settings.USDA_API_KEY
        """
        self.api_key = api_key or settings.USDA_API_KEY
        if not self.api_key:
            raise ValueError("USDA_API_KEY is required. Get one at https://fdc.nal.usda.gov/api-key-signup.html")

    async def search_foods(
        self,
        query: str,
        data_type: list[str] | None = None,
        page_size: int = 25,
        page_number: int = 1,
        brand_owner: str | None = None,
    ) -> dict[str, Any]:
        """Search for foods in USDA database.
        
        Args:
            query: Search query (e.g., "chicken breast", "brown rice")
            data_type: Filter by data type. Options: ["Foundation", "SR Legacy", "Survey (FNDDS)", "Branded"]
            page_size: Number of results per page (max 200)
            page_number: Page number (1-indexed)
            brand_owner: Filter by brand owner for branded foods
            
        Returns:
            Search results with foods matching the query
            
        Example:
            >>> client = USDAFoodDataClient()
            >>> results = await client.search_foods("chicken breast", data_type=["SR Legacy"])
            >>> for food in results["foods"]:
            ...     print(f"{food['description']}: {food['fdcId']}")
        """
        params = {
            "query": query,
            "pageSize": min(page_size, 200),
            "pageNumber": page_number,
            "api_key": self.api_key,
        }

        if data_type:
            params["dataType"] = data_type

        if brand_owner:
            params["brandOwner"] = brand_owner

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/foods/search", params=params)
            response.raise_for_status()
            return response.json()

    async def get_food_details(self, fdc_id: str | int) -> dict[str, Any]:
        """Get detailed nutritional information for a specific food.
        
        Args:
            fdc_id: USDA FoodData Central ID
            
        Returns:
            Detailed food information including all nutrients
            
        Example:
            >>> client = USDAFoodDataClient()
            >>> food = await client.get_food_details("173527")  # Chicken breast
            >>> print(f"Protein per 100g: {food['foodNutrients'][0]['amount']}g")
        """
        params = {"api_key": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/food/{fdc_id}", params=params)
            response.raise_for_status()
            return response.json()

    async def calculate_portions(
        self,
        fdc_id: str | int,
        quantity: float,
        unit: str = "g",
    ) -> dict[str, Any]:
        """Calculate nutritional values for a specific portion size.
        
        Args:
            fdc_id: USDA FoodData Central ID
            quantity: Quantity of food
            unit: Unit of measurement (g, oz, cup, etc.)
            
        Returns:
            Nutritional values scaled to the specified portion
            
        Example:
            >>> client = USDAFoodDataClient()
            >>> nutrition = await client.calculate_portions("173527", 200, "g")
            >>> print(f"Calories in 200g: {nutrition['calories']}")
        """
        food = await self.get_food_details(fdc_id)

        # Get base nutritional values per 100g
        nutrients = {}
        for nutrient in food.get("foodNutrients", []):
            name = nutrient.get("nutrient", {}).get("name")
            amount = nutrient.get("amount", 0)
            unit_name = nutrient.get("nutrient", {}).get("unitName", "")

            if name:
                nutrients[name] = {"amount": amount, "unit": unit_name}

        # Calculate scaling factor (assuming base is per 100g)
        if unit == "g":
            scale_factor = quantity / 100
        elif unit == "oz":
            # 1 oz = 28.35g
            scale_factor = (quantity * 28.35) / 100
        elif unit == "lb":
            # 1 lb = 453.592g
            scale_factor = (quantity * 453.592) / 100
        else:
            # For other units, assume the values are already correct
            scale_factor = 1.0

        # Scale all nutrient amounts
        scaled_nutrients = {}
        for name, data in nutrients.items():
            scaled_nutrients[name] = {
                "amount": data["amount"] * scale_factor,
                "unit": data["unit"],
            }

        # Extract key macronutrients for easy access
        result = {
            "fdc_id": fdc_id,
            "description": food.get("description", ""),
            "quantity": quantity,
            "unit": unit,
            "calories": scaled_nutrients.get("Energy", {}).get("amount", 0),
            "protein_grams": scaled_nutrients.get("Protein", {}).get("amount", 0),
            "carbs_grams": scaled_nutrients.get("Carbohydrate, by difference", {}).get("amount", 0),
            "fats_grams": scaled_nutrients.get("Total lipid (fat)", {}).get("amount", 0),
            "fiber_grams": scaled_nutrients.get("Fiber, total dietary", {}).get("amount", 0),
            "all_nutrients": scaled_nutrients,
        }

        return result

    async def search_and_calculate(
        self,
        query: str,
        quantity: float,
        unit: str = "g",
        data_type: list[str] | None = None,
    ) -> dict[str, Any]:
        """Convenience method: search for food and calculate nutritional values in one call.
        
        Args:
            query: Search query
            quantity: Quantity of food
            unit: Unit of measurement
            data_type: Filter by data type
            
        Returns:
            Nutritional values for the first matching food
            
        Example:
            >>> client = USDAFoodDataClient()
            >>> nutrition = await client.search_and_calculate("chicken breast", 200, "g")
            >>> print(f"Calories: {nutrition['calories']}, Protein: {nutrition['protein_grams']}g")
        """
        search_results = await self.search_foods(query, data_type=data_type, page_size=1)

        if not search_results.get("foods"):
            raise ValueError(f"No foods found for query: {query}")

        fdc_id = search_results["foods"][0]["fdcId"]
        return await self.calculate_portions(fdc_id, quantity, unit)


# Singleton instance
usda_client = USDAFoodDataClient() if settings.USDA_API_KEY else None
