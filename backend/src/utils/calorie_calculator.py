"""Calorie and macro calculation utilities.

Handles TDEE (Total Daily Energy Expenditure) calculation and macro distribution
based on user biometrics and goals.
"""

from src.ai.schemas import UserBiometrics


def calculate_bmr(age: int, biological_sex: str, height_cm: float, weight_kg: float) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation.
    
    This is the most accurate formula for modern populations.
    
    Args:
        age: Age in years
        biological_sex: 'male' or 'female'
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms
    
    Returns:
        BMR in calories per day
    
    Raises:
        ValueError: If biological_sex is not 'male' or 'female'
    """
    if biological_sex.lower() == "male":
        # Men: BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) + 5
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif biological_sex.lower() == "female":
        # Women: BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) - 161
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        raise ValueError(f"biological_sex must be 'male' or 'female', got: {biological_sex}")
    
    return bmr


def get_activity_multiplier(activity_level: str) -> float:
    """Get TDEE multiplier for activity level.
    
    Args:
        activity_level: One of: sedentary, lightly_active, moderately_active, 
                        very_active, extra_active
    
    Returns:
        Activity multiplier for TDEE calculation
    
    Raises:
        ValueError: If activity_level is invalid
    """
    multipliers = {
        "sedentary": 1.2,  # Little or no exercise
        "lightly_active": 1.375,  # Exercise 1-3 days/week
        "moderately_active": 1.55,  # Exercise 3-5 days/week
        "very_active": 1.725,  # Exercise 6-7 days/week
        "extra_active": 1.9,  # Athlete or very physical job
    }
    
    activity_level_lower = activity_level.lower()
    if activity_level_lower not in multipliers:
        raise ValueError(
            f"Invalid activity_level: {activity_level}. "
            f"Must be one of: {', '.join(multipliers.keys())}"
        )
    
    return multipliers[activity_level_lower]


def calculate_tdee(biometrics: UserBiometrics) -> float:
    """Calculate Total Daily Energy Expenditure.
    
    TDEE = BMR × Activity Multiplier
    
    Args:
        biometrics: User's biometric data
    
    Returns:
        TDEE in calories per day
    """
    bmr = calculate_bmr(
        age=biometrics.age,
        biological_sex=biometrics.biological_sex,
        height_cm=biometrics.height_cm,
        weight_kg=biometrics.weight_kg,
    )
    
    activity_multiplier = get_activity_multiplier(biometrics.activity_level)
    
    tdee = bmr * activity_multiplier
    
    return round(tdee)


def calculate_daily_calories(
    tdee: float,
    goal_modifier: float,
    day_modifier: float = 1.0
) -> int:
    """Calculate daily calorie target based on TDEE and modifiers.
    
    Args:
        tdee: Total Daily Energy Expenditure in calories
        goal_modifier: Goal adjustment (0.8-0.9 for cutting, 1.0 for maintenance, 1.1-1.2 for bulking)
        day_modifier: Day-specific adjustment (1.0 for training, 0.9 for rest, 1.1 for refeed)
    
    Returns:
        Daily calorie target
    """
    calories = tdee * goal_modifier * day_modifier
    return round(calories)


def calculate_macros_from_percentages(
    daily_calories: int,
    carbs_percent: int,
    protein_percent: int,
    fat_percent: int
) -> dict[str, int]:
    """Calculate macro grams from calorie percentages.
    
    Uses standard calorie per gram values:
    - Protein: 4 cal/g
    - Carbs: 4 cal/g
    - Fat: 9 cal/g
    
    Args:
        daily_calories: Total daily calories
        carbs_percent: Percentage of calories from carbs (0-100)
        protein_percent: Percentage of calories from protein (0-100)
        fat_percent: Percentage of calories from fat (0-100)
    
    Returns:
        Dict with keys: protein_grams, carbs_grams, fat_grams
    
    Raises:
        ValueError: If percentages don't sum to 100
    """
    total_percent = carbs_percent + protein_percent + fat_percent
    if total_percent != 100:
        raise ValueError(
            f"Macro percentages must sum to 100, got {total_percent} "
            f"(carbs={carbs_percent}, protein={protein_percent}, fat={fat_percent})"
        )
    
    # Calculate calories per macro
    protein_calories = (daily_calories * protein_percent) / 100
    carbs_calories = (daily_calories * carbs_percent) / 100
    fat_calories = (daily_calories * fat_percent) / 100
    
    # Convert to grams (protein: 4 cal/g, carbs: 4 cal/g, fat: 9 cal/g)
    protein_grams = round(protein_calories / 4)
    carbs_grams = round(carbs_calories / 4)
    fat_grams = round(fat_calories / 9)
    
    return {
        "protein_grams": protein_grams,
        "carbs_grams": carbs_grams,
        "fat_grams": fat_grams,
    }


def distribute_calories_to_meals(
    daily_calories: int,
    meal_percentages: list[float]
) -> list[int]:
    """Distribute daily calories across meals based on percentages.
    
    Args:
        daily_calories: Total daily calories
        meal_percentages: List of percentages for each meal (should sum to 100)
    
    Returns:
        List of calorie targets for each meal
    
    Raises:
        ValueError: If percentages don't sum to ~100
    """
    total_percent = sum(meal_percentages)
    if not (99 <= total_percent <= 101):  # Allow small rounding errors
        raise ValueError(
            f"Meal percentages should sum to 100, got {total_percent:.1f}"
        )
    
    # Distribute calories
    meal_calories = [
        round((daily_calories * pct) / 100)
        for pct in meal_percentages
    ]
    
    # Adjust last meal to hit exact total (handles rounding)
    difference = daily_calories - sum(meal_calories)
    meal_calories[-1] += difference
    
    return meal_calories


def distribute_meal_calories_to_foods(
    meal_calories: int,
    food_percentages: list[float]
) -> list[int]:
    """Distribute meal calories across food items based on percentages.
    
    Args:
        meal_calories: Total meal calories
        food_percentages: List of percentages for each food item (should sum to 100)
    
    Returns:
        List of calorie amounts for each food item
    
    Raises:
        ValueError: If percentages don't sum to ~100
    """
    total_percent = sum(food_percentages)
    if not (99 <= total_percent <= 101):  # Allow small rounding errors
        raise ValueError(
            f"Food percentages should sum to 100, got {total_percent:.1f}"
        )
    
    # Distribute calories
    food_calories = [
        round((meal_calories * pct) / 100)
        for pct in food_percentages
    ]
    
    # Adjust last food to hit exact total (handles rounding)
    difference = meal_calories - sum(food_calories)
    food_calories[-1] += difference
    
    return food_calories


# Example usage and validation
if __name__ == "__main__":
    # Example user
    biometrics = UserBiometrics(
        age=30,
        biological_sex="male",
        height_cm=180,
        weight_kg=80,
        activity_level="moderately_active"
    )
    
    # Calculate TDEE
    tdee = calculate_tdee(biometrics)
    print(f"TDEE: {tdee} calories/day")
    
    # Bulking phase (+15% calories)
    bulk_calories = calculate_daily_calories(tdee, goal_modifier=1.15)
    print(f"Bulking calories: {bulk_calories}/day")
    
    # Calculate macros (40% carbs, 30% protein, 30% fat)
    macros = calculate_macros_from_percentages(
        bulk_calories,
        carbs_percent=40,
        protein_percent=30,
        fat_percent=30
    )
    print(f"Macros: {macros}")
    
    # Distribute to meals (30%, 25%, 20%, 25% for 4 meals)
    meal_cals = distribute_calories_to_meals(
        bulk_calories,
        [30, 25, 20, 25]
    )
    print(f"Meal calories: {meal_cals}")
