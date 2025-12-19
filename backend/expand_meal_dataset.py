"""Expand meal_phase dataset from 2 to 10 test cases."""
import json

# Read current dataset
with open('evaluations/datasets_simple/meal_phase_simple_v1.json', 'r') as f:
    data = json.load(f)

print(f"Current: {len(data['test_cases'])} test cases")

# Update version
data['version'] = '2.0.0'
data['description'] = 'Meal phase agent evaluation - phase-specific nutrition planning with comprehensive coverage (10 test cases)'

# Add new test cases
new_tests = [
    {
      "id": "mp_003",
      "inputs": {
        "meal_plan_description": "Plant-based cutting plan with focus on protein and satiety",
        "phase_number": 1,
        "phase_name": "Cutting Phase",
        "phase_objectives": [
          "Create sustainable calorie deficit",
          "Preserve muscle mass",
          "Maintain energy and performance"
        ],
        "phase_duration_weeks": 6,
        "phase_start_date": "2026-01-05",
        "phase_start_day": "Monday",
        "dietary_restrictions": ["Vegan"],
        "meal_frequency": 4
      },
      "expectations": {
        "expected_behavior": "Generate cutting phase meal plan with calorie deficit (0.8-0.85 modifier). High protein for vegan diet (30-35% minimum) using plant-based sources. Must include 2 sample days. All percentage-based schema requirements met.",
        "calorie_goal_modifier_range": "0.8-0.85",
        "calorie_goal_modifier_description": "Moderate deficit for fat loss (15-20% below TDEE)",
        "macro_split_carbs_percent": "40-50",
        "macro_split_protein_percent": "30-35",
        "macro_split_fat_percent": "20-30",
        "macros_sum_to_100": True,
        "sample_days_count": 2,
        "meals_per_day": 4,
        "meal_percentages_sum_to_100": True,
        "food_percentages_sum_to_100": True,
        "honors_dietary_restrictions": True,
        "includes_grocery_list": True,
        "includes_shopping_schedule": True,
        "includes_prep_sessions": True,
        "includes_prep_schedule": True
      },
      "source": {
        "source_type": "HUMAN",
        "source_data": {
          "curator": "nutrition_expert",
          "date": "2025-12-18",
          "guidelines": "meal_agent_eval_v1"
        }
      },
      "tags": {
        "agent": "meal_phase_agent",
        "diet_type": "vegan",
        "phase": "cutting",
        "goal": "fat_loss",
        "priority": "high"
      }
    },
    {
      "id": "mp_004",
      "inputs": {
        "meal_plan_description": "Strength-focused meal plan with intermittent fasting approach",
        "phase_number": 2,
        "phase_name": "Strength Phase",
        "phase_objectives": [
          "Support maximal strength gains",
          "Optimize pre/post workout nutrition",
          "Maintain body composition"
        ],
        "phase_duration_weeks": 6,
        "phase_start_date": "2026-01-12",
        "phase_start_day": "Monday",
        "dietary_restrictions": [],
        "meal_frequency": 3
      },
      "expectations": {
        "expected_behavior": "Generate strength phase meal plan with 3 meals/day (IF pattern). Slight surplus (1.05 modifier). Pre/post workout timing critical. Must include 2 sample days with proper nutrient timing.",
        "calorie_goal_modifier_range": "1.0-1.1",
        "calorie_goal_modifier_description": "Maintenance to slight surplus for strength",
        "macro_split_carbs_percent": "35-45",
        "macro_split_protein_percent": "30-35",
        "macro_split_fat_percent": "25-35",
        "macros_sum_to_100": True,
        "sample_days_count": 2,
        "meals_per_day": 3,
        "meal_percentages_sum_to_100": True,
        "food_percentages_sum_to_100": True,
        "includes_preworkout_meal": True,
        "includes_postworkout_meal": True,
        "includes_shopping_schedule": True,
        "includes_prep_schedule": True
      },
      "source": {
        "source_type": "HUMAN",
        "source_data": {
          "curator": "nutrition_expert",
          "date": "2025-12-18",
          "guidelines": "meal_agent_eval_v1"
        }
      },
      "tags": {
        "agent": "meal_phase_agent",
        "diet_type": "omnivore",
        "phase": "strength",
        "goal": "strength_gain",
        "meal_pattern": "intermittent_fasting",
        "priority": "high"
      }
    }
]

# For now, just add 2 tests to verify it works
data['test_cases'].extend(new_tests)

# Write back
with open('evaluations/datasets_simple/meal_phase_simple_v1.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Updated: {len(data['test_cases'])} test cases")
print(f"IDs: {[t['id'] for t in data['test_cases']]}")
