# Calorie Calculation Architecture Change

**Date:** December 18, 2025  
**Status:** Schemas updated, utilities created, agents need updates

## Overview

Changed from agents calculating exact calories to agents providing percentages/ratios, with code handling all math.

## Motivation

**Problems with old approach:**
- ❌ LLMs are bad at math
- ❌ Agents often missed calorie targets (meal_phase_agent: 2900 cal when 3000-3400 expected)
- ❌ Hard to validate correctness
- ❌ Not personalized to individual user's metabolism

**Benefits of new approach:**
- ✅ Agents focus on strategy/ratios (what they're good at)
- ✅ Code handles precise calculations (what it's good at)
- ✅ Automatically personalized via TDEE
- ✅ Easy to validate (percentages sum to 100%)
- ✅ More accurate and consistent

## What Changed

### 1. Schemas Updated

**Old structure (agent calculates):**
```python
daily_calorie_target: int = 3200  # Agent guesses
macro_split: str = "40% Carbs, 30% Protein, 30% Fat"  # String
MealItem: calories: int = 450  # Agent calculates
```

**New structure (agent provides ratios):**
```python
calorie_goal_modifier: float = 1.15  # 15% surplus for bulking
macro_split_carbs_percent: int = 40  # Percentage
macro_split_protein_percent: int = 30
macro_split_fat_percent: int = 30
MealItem: calorie_percentage: float = 25.0  # % of meal calories
```

### 2. Biometric Data Collection

**New field in ConversationRequirements:**
```python
class UserBiometrics(BaseModel):
    age: int
    biological_sex: str  # 'male' or 'female'
    height_cm: float
    weight_kg: float
    activity_level: str  # 'sedentary', 'lightly_active', etc.
```

### 3. Calorie Calculator Utility

**Created:** `src/utils/calorie_calculator.py`

**Functions:**
- `calculate_bmr()` - Mifflin-St Jeor equation
- `calculate_tdee()` - BMR × activity multiplier
- `calculate_daily_calories()` - TDEE × goal modifier × day modifier
- `calculate_macros_from_percentages()` - Convert macro % to grams
- `distribute_calories_to_meals()` - Meal calorie targets from %
- `distribute_meal_calories_to_foods()` - Food item calories from %

## Agent Updates Needed

### 1. Intake Specialist Agent

**File:** `src/ai/app_agents/intake_specialist_agent.py`

**Changes needed:**
```python
# OLD questions:
"What's your primary fitness goal?"
"How many days per week can you work out?"

# NEW questions (add biometrics):
"What's your age?"
"What's your biological sex (for metabolism calculation)?"
"What's your height?" (convert to cm if needed)
"What's your weight?" (convert to kg if needed)
"How would you describe your activity level?"
  - Sedentary (little/no exercise)
  - Lightly active (exercise 1-3 days/week)
  - Moderately active (exercise 3-5 days/week)
  - Very active (exercise 6-7 days/week)
  - Extra active (athlete/physical job)
```

**Output:** Must now include `UserBiometrics` in `ConversationRequirements`

### 2. Meal Phase Agent

**File:** `src/ai/app_agents/meal_phase_agent.py`

**Changes needed:**

**OLD prompt:**
```
Generate meal plan with:
- daily_calorie_target: 3200
- macro_split: "40% Carbs, 30% Protein, 30% Fat"
```

**NEW prompt:**
```
Generate meal plan with:
- calorie_goal_modifier: 1.15 (for 15% surplus)
- macro_split_carbs_percent: 40
- macro_split_protein_percent: 30
- macro_split_fat_percent: 30

For each meal:
- Provide calorie_percentage (e.g., 30% for breakfast)
- All meals should sum to 100%

For each food item in meals:
- Provide calorie_percentage (e.g., 40% chicken, 35% rice, 25% veggies)
- All foods in meal should sum to 100%
```

**Critical instructions to add:**
```
⚠️ CRITICAL: Your job is to decide RATIOS and PERCENTAGES, not absolute calories.

DO NOT calculate exact calories - code will handle that based on user's TDEE.

Your responsibilities:
1. Decide calorie goal strategy (cutting/maintaining/bulking as 0.8-1.2 modifier)
2. Decide macro split percentages (must sum to 100%)
3. Decide meal calorie distribution percentages (must sum to 100%)
4. Decide food calorie distribution within meals (must sum to 100%)

Code will handle:
- Calculating user's TDEE from biometrics
- Applying your modifiers to get exact calories
- Distributing calories to meals/foods based on your percentages
- Converting macro percentages to grams
```

### 3. Fitness Coach Agent (future)

**File:** `src/ai/app_agents/fitness_coach_agent.py`

Will need updates when users want to:
- Update their weight (recalculate TDEE)
- Change goals (adjust calorie modifier)
- Modify macro split

### 4. Build Fitness Plan Function

**File:** `src/ai/tools/plan_tools.py` (or wherever build_fitness_plan is)

**Changes needed:**
1. Accept `ConversationRequirements` with `biometrics`
2. Calculate TDEE: `tdee = calculate_tdee(requirements.biometrics)`
3. Pass TDEE to meal generation
4. After agent generates plan with percentages, expand to actual numbers:

```python
from src.utils.calorie_calculator import (
    calculate_tdee,
    calculate_daily_calories,
    calculate_macros_from_percentages,
    distribute_calories_to_meals,
    distribute_meal_calories_to_foods
)

# Calculate user's TDEE
tdee = calculate_tdee(requirements.biometrics)

# For each phase:
for phase in fitness_plan.phases:
    meal_details = phase.meal_details
    
    # Calculate daily calories for this phase
    daily_calories = calculate_daily_calories(
        tdee=tdee,
        goal_modifier=meal_details.calorie_goal_modifier
    )
    
    # Calculate macros
    macros = calculate_macros_from_percentages(
        daily_calories=daily_calories,
        carbs_percent=meal_details.macro_split_carbs_percent,
        protein_percent=meal_details.macro_split_protein_percent,
        fat_percent=meal_details.macro_split_fat_percent
    )
    
    # For each sample day:
    for day in meal_details.sample_days:
        # Apply day modifier (training vs rest)
        day_calories = calculate_daily_calories(
            tdee=tdee,
            goal_modifier=meal_details.calorie_goal_modifier,
            day_modifier=day.calorie_modifier
        )
        
        # Get meal percentages
        meal_percentages = [meal.calorie_percentage for meal in day.meals]
        
        # Distribute to meals
        meal_calorie_targets = distribute_calories_to_meals(
            daily_calories=day_calories,
            meal_percentages=meal_percentages
        )
        
        # For each meal:
        for meal, meal_calories in zip(day.meals, meal_calorie_targets):
            # Get food percentages
            food_percentages = [food.calorie_percentage for food in meal.foods]
            
            # Distribute to foods
            food_calorie_targets = distribute_meal_calories_to_foods(
                meal_calories=meal_calories,
                food_percentages=food_percentages
            )
            
            # Assign to food items
            for food, food_calories in zip(meal.foods, food_calorie_targets):
                # Store calculated calories (maybe extend schema with calculated fields)
                # Or calculate on-the-fly when needed
                pass
```

## Database Schema Impact

**Current schema:** Already has fields for calculated values:
- `meal_plans.daily_calorie_target`
- `meal_plans.protein_grams_target`
- `meal_plans.carbs_grams_target`
- `meal_plans.fats_grams_target`
- `meals.calories`
- `meals.protein_grams`
- `meals.carbs_grams`
- `meals.fats_grams`

**Strategy:** Keep these fields for storing calculated values. Add new fields for agent outputs:
- `meal_plans.calorie_goal_modifier` (float)
- `meal_plans.macro_carbs_percent` (int)
- `meal_plans.macro_protein_percent` (int)
- `meal_plans.macro_fats_percent` (int)

**Migration needed:** Yes, to add new fields. Can be nullable initially.

## Testing Strategy

### 1. Unit Tests for Calculator
```python
def test_calculate_tdee():
    biometrics = UserBiometrics(
        age=30, biological_sex="male",
        height_cm=180, weight_kg=80,
        activity_level="moderately_active"
    )
    tdee = calculate_tdee(biometrics)
    assert 2400 <= tdee <= 2800  # Reasonable range

def test_macro_percentages_sum_to_100():
    with pytest.raises(ValueError):
        calculate_macros_from_percentages(
            2500, carbs_percent=40, protein_percent=40, fat_percent=30
        )  # Sums to 110%
```

### 2. Integration Test for Meal Generation
- Mock user with known biometrics
- Generate meal plan
- Verify percentages sum correctly
- Verify calculated calories are reasonable
- Verify macro grams match percentages

### 3. Evaluation Dataset Updates
Update meal_phase test cases to expect:
- `calorie_goal_modifier` instead of `daily_calorie_target`
- Separate macro percent fields instead of string
- `calorie_percentage` fields instead of absolute calories

## Rollout Plan

1. ✅ **Update schemas** - DONE
2. ✅ **Create calculator utilities** - DONE
3. ⏳ **Update intake_specialist_agent** - Collect biometrics
4. ⏳ **Update meal_phase_agent** - Generate percentages
5. ⏳ **Update build_fitness_plan** - Calculate actual values
6. ⏳ **Update database schema** - Add new fields
7. ⏳ **Update evaluation datasets** - New expected outputs
8. ⏳ **Re-run evaluations** - Verify improvements
9. ⏳ **Update fitness_coach_agent** - Handle weight updates

## Expected Results

After changes:
- **Meal phase agent** should get "excellent" ratings (currently "poor" due to missed calorie targets)
- **Calorie targets** automatically accurate for any user
- **Math errors** eliminated
- **Personalization** improved via TDEE calculation

## Next Steps

1. Update intake_specialist_agent to collect biometrics
2. Update meal_phase_agent prompt to generate percentages
3. Test with evaluation
4. Document results

---

*This represents a significant architectural improvement that moves math operations from LLMs (unreliable) to code (reliable).*
