"""Create expanded meal_phase dataset with 10 test cases using MLflow API."""
import mlflow
from mlflow.genai.datasets import create_dataset

# Set MLflow tracking URI to match evaluation script
mlflow.set_tracking_uri("http://localhost:5000")

# Create dataset - using list format like MLflow docs recommend
dataset = create_dataset(
    name="meal_phase_simple_v1",
    experiment_id=["5"],  # meal_phase_agent experiment - must be list format
    tags={"version": "2.0.0", "coverage": "comprehensive"},
)

# Define all 10 test cases
test_cases = [
    # mp_001: Foundation Phase - Pescatarian, No Dairy
    {
        "inputs": {
            "meal_plan_description": "Mediterranean-style nutrition plan for muscle building with emphasis on whole foods",
            "phase_number": 1,
            "phase_name": "Foundation Phase",
            "phase_objectives": [
                "Establish baseline calories",
                "Build healthy eating habits",
                "Assess metabolic response"
            ],
            "phase_duration_weeks": 4,
            "phase_start_date": "2025-12-15",
            "phase_start_day": "Sunday",
            "dietary_restrictions": ["No dairy", "Pescatarian"],
            "meal_frequency": 4
        },
        "expectations": {
            "expected_behavior": "Generate phase-specific meal plan with 4 meals/day for pescatarian with no dairy. Foundation phase should use maintenance calories (calorie_goal_modifier: 1.0). Include 2 sample days (training + rest). Must include grocery list with categories and shopping schedule. Must include meal prep sessions with instructions and prep schedule. All schedules use target_day_name format. Use percentage-based schema (calorie_goal_modifier, macro_split_*_percent, calorie_percentage for meals/foods).",
            "calorie_goal_modifier_range": "0.95-1.05",
            "calorie_goal_modifier_description": "Maintenance calories for foundation phase",
            "macro_split_carbs_percent": "35-45",
            "macro_split_protein_percent": "25-35",
            "macro_split_fat_percent": "25-35",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 4,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "honors_dietary_restrictions": True,
            "includes_grocery_list": True,
            "includes_shopping_schedule": True,
            "includes_prep_sessions": True,
            "includes_prep_schedule": True,
            "schedule_uses_day_names": True
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-17", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "pescatarian", "dietary_restrictions": "no_dairy", "phase": "foundation", "priority": "high"}
    },
    # mp_002: Hypertrophy Phase - Omnivore
    {
        "inputs": {
            "meal_plan_description": "High-protein meal plan for hypertrophy with calorie surplus",
            "phase_number": 2,
            "phase_name": "Hypertrophy Phase",
            "phase_objectives": ["Maximize muscle growth", "Maintain calorie surplus", "Optimize protein timing"],
            "phase_duration_weeks": 8,
            "phase_start_date": "2025-12-22",
            "phase_start_day": "Sunday",
            "dietary_restrictions": [],
            "meal_frequency": 5
        },
        "expectations": {
            "expected_behavior": "Generate hypertrophy phase meal plan with 5 meals/day. Should use calorie surplus modifier (1.1-1.2 for 10-20% surplus). High protein (35-40% of calories). Include pre/post workout nutrition. Must include complete grocery shopping and meal prep schedules with explicit day names and repeat patterns. Use percentage-based schema (calorie_goal_modifier, macro_split_*_percent fields, calorie_percentage for meals/foods - all must sum to 100%).",
            "calorie_goal_modifier_range": "1.1-1.2",
            "calorie_goal_modifier_description": "Calorie surplus for muscle building (10-20% above TDEE)",
            "macro_split_carbs_percent": "35-45",
            "macro_split_protein_percent": "35-40",
            "macro_split_fat_percent": "20-30",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 5,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "includes_preworkout_meal": True,
            "includes_postworkout_meal": True,
            "includes_shopping_schedule": True,
            "includes_prep_schedule": True,
            "schedule_format": "day_name_with_repeats"
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-17", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "omnivore", "phase": "hypertrophy", "goal": "muscle_growth", "priority": "high"}
    },
    # mp_003: Cutting Phase - Vegan
    {
        "inputs": {
            "meal_plan_description": "Plant-based cutting plan with focus on protein and satiety",
            "phase_number": 1,
            "phase_name": "Cutting Phase",
            "phase_objectives": ["Create sustainable calorie deficit", "Preserve muscle mass", "Maintain energy and performance"],
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
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "vegan", "phase": "cutting", "goal": "fat_loss", "priority": "high"}
    },
    # mp_004: Strength Phase - IF
    {
        "inputs": {
            "meal_plan_description": "Strength-focused meal plan with intermittent fasting approach",
            "phase_number": 2,
            "phase_name": "Strength Phase",
            "phase_objectives": ["Support maximal strength gains", "Optimize pre/post workout nutrition", "Maintain body composition"],
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
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "omnivore", "phase": "strength", "goal": "strength_gain", "meal_pattern": "intermittent_fasting", "priority": "high"}
    },
    # mp_005: Aggressive Cut - Vegetarian + Gluten-Free
    {
        "inputs": {
            "meal_plan_description": "Aggressive cutting protocol for vegetarian with gluten sensitivity",
            "phase_number": 1,
            "phase_name": "Aggressive Cut Phase",
            "phase_objectives": ["Maximize fat loss rate", "Preserve lean mass", "Manage hunger effectively"],
            "phase_duration_weeks": 4,
            "phase_start_date": "2026-02-01",
            "phase_start_day": "Saturday",
            "dietary_restrictions": ["Vegetarian", "Gluten-free"],
            "meal_frequency": 5
        },
        "expectations": {
            "expected_behavior": "Generate aggressive cutting meal plan with high deficit (0.7-0.75 modifier). Very high protein for vegetarian (35-40%). 5 smaller meals for satiety. Gluten-free compliant. Must handle multiple dietary restrictions.",
            "calorie_goal_modifier_range": "0.7-0.75",
            "calorie_goal_modifier_description": "Aggressive deficit for rapid fat loss (25-30% below TDEE)",
            "macro_split_carbs_percent": "30-40",
            "macro_split_protein_percent": "35-40",
            "macro_split_fat_percent": "25-30",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 5,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "honors_dietary_restrictions": True,
            "includes_grocery_list": True,
            "includes_shopping_schedule": True,
            "includes_prep_schedule": True
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "vegetarian", "phase": "cutting", "goal": "aggressive_fat_loss", "dietary_restrictions": "gluten_free", "priority": "high"}
    },
    # mp_006: Keto Hypertrophy - Extreme Macro Split
    {
        "inputs": {
            "meal_plan_description": "Ketogenic approach to muscle building with extreme macro ratios",
            "phase_number": 2,
            "phase_name": "Keto Hypertrophy Phase",
            "phase_objectives": ["Build muscle in ketosis", "Maintain metabolic flexibility", "Optimize fat adaptation"],
            "phase_duration_weeks": 8,
            "phase_start_date": "2026-02-15",
            "phase_start_day": "Sunday",
            "dietary_restrictions": [],
            "meal_frequency": 4
        },
        "expectations": {
            "expected_behavior": "Generate ketogenic hypertrophy plan with extreme low carbs (5-10%), high fat (60-70%), moderate-high protein (25-30%). Calorie surplus for muscle growth. Must sum to 100%.",
            "calorie_goal_modifier_range": "1.1-1.15",
            "calorie_goal_modifier_description": "Moderate surplus for muscle growth on keto",
            "macro_split_carbs_percent": "5-10",
            "macro_split_protein_percent": "25-30",
            "macro_split_fat_percent": "60-70",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 4,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "includes_grocery_list": True,
            "includes_shopping_schedule": True,
            "includes_prep_schedule": True
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "keto", "phase": "hypertrophy", "goal": "muscle_growth", "macro_pattern": "extreme", "priority": "high"}
    },
    # mp_007: Foundation with Allergies - 6 Meals
    {
        "inputs": {
            "meal_plan_description": "Foundation phase with multiple food allergies requiring careful planning",
            "phase_number": 1,
            "phase_name": "Foundation Phase",
            "phase_objectives": ["Establish baseline", "Identify safe foods", "Build consistent routine"],
            "phase_duration_weeks": 6,
            "phase_start_date": "2026-03-01",
            "phase_start_day": "Saturday",
            "dietary_restrictions": ["No shellfish", "No tree nuts", "Lactose intolerant"],
            "meal_frequency": 6
        },
        "expectations": {
            "expected_behavior": "Generate foundation phase with 6 smaller meals. Handle multiple allergies safely. Maintenance calories. High meal frequency tests percentage distribution across many meals.",
            "calorie_goal_modifier_range": "0.95-1.05",
            "calorie_goal_modifier_description": "Maintenance for foundation",
            "macro_split_carbs_percent": "35-45",
            "macro_split_protein_percent": "25-35",
            "macro_split_fat_percent": "25-35",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 6,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "honors_dietary_restrictions": True,
            "includes_grocery_list": True,
            "includes_shopping_schedule": True,
            "includes_prep_schedule": True
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "omnivore", "phase": "foundation", "dietary_restrictions": "multiple_allergies", "meal_frequency": "high", "priority": "high"}
    },
    # mp_008: Budget Cutting - Minimal Prep
    {
        "inputs": {
            "meal_plan_description": "Budget-friendly cutting plan with minimal meal prep requirements",
            "phase_number": 1,
            "phase_name": "Budget Cutting Phase",
            "phase_objectives": ["Achieve fat loss on budget", "Minimize prep time", "Use accessible ingredients"],
            "phase_duration_weeks": 6,
            "phase_start_date": "2026-03-15",
            "phase_start_day": "Monday",
            "dietary_restrictions": [],
            "meal_frequency": 3
        },
        "expectations": {
            "expected_behavior": "Generate budget-conscious cutting plan. Moderate deficit. Simple, accessible foods. Minimal prep complexity. Must still meet all percentage-based requirements.",
            "calorie_goal_modifier_range": "0.8-0.85",
            "calorie_goal_modifier_description": "Moderate deficit for sustainable fat loss",
            "macro_split_carbs_percent": "35-45",
            "macro_split_protein_percent": "30-35",
            "macro_split_fat_percent": "25-30",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 3,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "includes_grocery_list": True,
            "includes_shopping_schedule": True,
            "includes_prep_schedule": True
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "omnivore", "phase": "cutting", "goal": "fat_loss", "constraint": "budget", "priority": "medium"}
    },
    # mp_009: Maintenance - Pescatarian + Gluten Sensitive
    {
        "inputs": {
            "meal_plan_description": "Maintenance phase for pescatarian with gluten sensitivity",
            "phase_number": 3,
            "phase_name": "Maintenance Phase",
            "phase_objectives": ["Maintain current composition", "Sustain energy levels", "Establish long-term habits"],
            "phase_duration_weeks": 8,
            "phase_start_date": "2026-04-01",
            "phase_start_day": "Tuesday",
            "dietary_restrictions": ["Pescatarian", "Gluten-sensitive"],
            "meal_frequency": 4
        },
        "expectations": {
            "expected_behavior": "Generate maintenance phase at TDEE (1.0 modifier). Pescatarian with gluten-sensitive options. Balanced macros. Long-term sustainability focus.",
            "calorie_goal_modifier_range": "0.95-1.05",
            "calorie_goal_modifier_description": "Maintenance calories at TDEE",
            "macro_split_carbs_percent": "35-45",
            "macro_split_protein_percent": "25-35",
            "macro_split_fat_percent": "25-35",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 4,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "honors_dietary_restrictions": True,
            "includes_grocery_list": True,
            "includes_shopping_schedule": True,
            "includes_prep_schedule": True
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "pescatarian", "phase": "maintenance", "dietary_restrictions": "gluten_sensitive", "priority": "medium"}
    },
    # mp_010: Performance - Vegan Endurance Athlete
    {
        "inputs": {
            "meal_plan_description": "High-carb vegan nutrition for endurance performance",
            "phase_number": 2,
            "phase_name": "Performance Phase",
            "phase_objectives": ["Fuel endurance training", "Optimize recovery", "Maintain plant-based nutrition"],
            "phase_duration_weeks": 10,
            "phase_start_date": "2026-04-20",
            "phase_start_day": "Sunday",
            "dietary_restrictions": ["Vegan"],
            "meal_frequency": 5
        },
        "expectations": {
            "expected_behavior": "Generate high-carb vegan performance plan. Higher carbs (50-55%) for endurance. Adequate plant protein (25-30%). Slight surplus for training volume. 5 meals for consistent fueling.",
            "calorie_goal_modifier_range": "1.05-1.15",
            "calorie_goal_modifier_description": "Slight surplus to fuel endurance training volume",
            "macro_split_carbs_percent": "50-55",
            "macro_split_protein_percent": "25-30",
            "macro_split_fat_percent": "20-25",
            "macros_sum_to_100": True,
            "sample_days_count": 2,
            "meals_per_day": 5,
            "meal_percentages_sum_to_100": True,
            "food_percentages_sum_to_100": True,
            "honors_dietary_restrictions": True,
            "includes_grocery_list": True,
            "includes_shopping_schedule": True,
            "includes_prep_schedule": True
        },
        "source": {"source_type": "HUMAN", "source_data": {"curator": "nutrition_expert", "date": "2025-12-18", "guidelines": "meal_agent_eval_v1"}},
        "tags": {"agent": "meal_phase_agent", "diet_type": "vegan", "phase": "performance", "goal": "endurance", "priority": "high"}
    },
]

# Merge records into dataset
dataset.merge_records(test_cases)

print(f"✅ Created dataset with {len(test_cases)} test cases")
print(f"Dataset name: {dataset.name}")
print(f"Dataset ID: {dataset.dataset_id}")
print(f"\nTest cases:")
for tc in test_cases:
    inputs = tc['inputs']
    restrictions = inputs.get('dietary_restrictions', [])
    diet_str = ', '.join(restrictions) if restrictions else 'omnivore'
    print(f"  - {inputs['phase_name']}: {diet_str}, {inputs['meal_frequency']} meals")
