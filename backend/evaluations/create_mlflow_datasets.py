"""Create MLflow-compatible evaluation datasets.

Format matches MLflow 3.7.0 schema:
- inputs: dict
- expectations: flat dict (NOT array)
- source: dict with source_type and source_data
- tags: flat dict
"""

import json
from pathlib import Path
from datetime import datetime


# Workout Phase Agent Dataset
workout_phase_dataset = {
    "name": "workout_phase_simple_v1",
    "version": "1.0.2",
    "description": "Workout phase agent evaluation - MLflow compatible format",
    "test_cases": [
        {
            "id": "wp_001",
            "inputs": {
                "workout_plan_description": "3-day per week full-body strength training for beginner",
                "phase_number": 1,
                "phase_name": "Foundation Phase",
                "phase_objectives": ["Build foundational strength", "Learn proper form", "Establish habit"],
                "phase_duration_weeks": 4,
                "fitness_level": "beginner",
                "equipment_access": ["barbell", "dumbbells", "bench", "squat_rack"],
                "workout_frequency": 3
            },
            "expectations": {
                "expected_behavior": "Generate 3 full-body workouts with 6-8 exercises focusing on compound movements (squat, deadlift, bench, rows). Beginner volume (3 sets x 8-12 reps). Workout cycle: 3 training + 4 rest days. Intensity: RPE 6-7. Volume: low-moderate for adaptation. Progression: linear (add weight weekly).",
                "workouts_count": 3,
                "exercises_per_workout_min": 6,
                "exercises_per_workout_max": 8,
                "has_compound_movements": True,
                "appropriate_for_beginner": True,
                "workout_cycle_length": 7,
                "intensity_level": "moderate"
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "fitness_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "fitness_agent_eval_v1"
                }
            },
            "tags": {
                "agent": "workout_phase_agent",
                "fitness_level": "beginner",
                "program_type": "full_body",
                "priority": "high"
            }
        },
        {
            "id": "wp_002",
            "inputs": {
                "workout_plan_description": "4-day upper/lower split for muscle growth",
                "phase_number": 2,
                "phase_name": "Hypertrophy Phase",
                "phase_objectives": ["Maximize muscle growth", "Increase volume", "Refine mind-muscle connection"],
                "phase_duration_weeks": 8,
                "fitness_level": "intermediate",
                "equipment_access": ["full_gym"],
                "workout_frequency": 4
            },
            "expectations": {
                "expected_behavior": "Generate 4 workouts (2 upper, 2 lower) for hypertrophy. Upper: 8-10 exercises (chest/back/shoulders/arms). Lower: 7-9 exercises (quads/hamstrings/glutes/calves). Volume: 3-4 sets x 8-12 reps. Workout cycle: alternating upper/lower with rest. Intensity: RPE 7-8. Volume: 16-20 sets per muscle/week. Progression: reps then weight.",
                "workouts_count": 4,
                "upper_lower_split": True,
                "hypertrophy_rep_range": True,
                "appropriate_volume": True,
                "intensity_level": "moderate-high"
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "fitness_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "fitness_agent_eval_v1"
                }
            },
            "tags": {
                "agent": "workout_phase_agent",
                "fitness_level": "intermediate",
                "program_type": "upper_lower",
                "priority": "high"
            }
        }
    ]
}

# Intake Agent Dataset
intake_dataset = {
    "name": "intake_simple_v1",
    "version": "1.0.2",
    "description": "Intake agent evaluation - MLflow compatible format",
    "test_cases": [
        {
            "id": "intake_001",
            "inputs": {
                "messages": [
                    {"role": "user", "content": "Hi, I want to get in shape. I've never really worked out before but I have access to a gym."}
                ]
            },
            "expectations": {
                "expected_behavior": "Warmly welcome user, acknowledge beginner status and gym access. Ask clarifying questions about goal, activity level, injuries, time availability. Be encouraging, not overwhelming. Ask 1-2 questions at a time.",
                "tone": "warm, encouraging, professional",
                "asks_questions": True,
                "asks_about_goals": True,
                "appropriate_for_beginner": True,
                "does_not_create_plan_yet": True,
                "question_count_max": 2
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "conversational_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "conversation_eval_v1"
                }
            },
            "tags": {
                "agent": "conversation_agent",
                "mode": "intake",
                "user_type": "beginner",
                "stage": "initial_contact",
                "priority": "high"
            }
        },
        {
            "id": "intake_002",
            "inputs": {
                "messages": [
                    {"role": "user", "content": "I want to build muscle. I'm 28, never lifted before, and I can train 4 days a week for about an hour each session. I have access to a full gym. No injuries."}
                ]
            },
            "expectations": {
                "expected_behavior": "Recognize comprehensive info provided. Summarize: muscle building, beginner, 4x/week, 1hr sessions, full gym, no injuries. Ask if ready to create plan or any other preferences. Positive, action-oriented tone.",
                "summarizes_user_info": True,
                "ready_to_proceed": True,
                "asks_confirmation": True,
                "tone": "positive, action-oriented",
                "acknowledges_all_info": True,
                "offers_to_create_plan": True
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "conversational_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "conversation_eval_v1"
                }
            },
            "tags": {
                "agent": "conversation_agent",
                "mode": "intake",
                "user_type": "beginner",
                "stage": "ready_to_build",
                "priority": "high"
            }
        }
    ]
}

# Fitness Coach Agent Dataset
coach_dataset = {
    "name": "fitness_coach_simple_v1",
    "version": "1.0.2",
    "description": "Fitness coach agent evaluation - MLflow compatible format",
    "test_cases": [
        {
            "id": "coach_001",
            "inputs": {
                "messages": [
                    {"role": "user", "content": "What workouts do I have this week?"}
                ],
                "user_context": {
                    "has_active_plan": True,
                    "plan_name": "12-Week Muscle Building Program",
                    "current_phase": "Foundation Phase",
                    "current_week": 2
                }
            },
            "expectations": {
                "expected_behavior": "Use query_agent to retrieve workout schedule for current week. Present info clearly. Ask if user wants more details. Be encouraging and supportive.",
                "uses_query_agent": True,
                "presents_workout_schedule": True,
                "offers_more_details": True,
                "tone": "encouraging, supportive",
                "provides_clear_answer": True
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "coach_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "coaching_eval_v1"
                }
            },
            "tags": {
                "agent": "conversation_agent",
                "mode": "coaching",
                "interaction_type": "plan_query",
                "priority": "high"
            }
        },
        {
            "id": "coach_002",
            "inputs": {
                "messages": [
                    {"role": "user", "content": "I hurt my shoulder doing overhead press yesterday. Can we modify my workouts to avoid shoulder pain?"}
                ],
                "user_context": {
                    "has_active_plan": True,
                    "plan_name": "Upper/Lower Split",
                    "current_phase": "Building Phase"
                }
            },
            "expectations": {
                "expected_behavior": "Express concern about injury. Recommend healthcare provider if severe. Offer to modify plan - avoid overhead pressing, suggest shoulder-friendly alternatives. Ask about pain severity and range of motion. Cautious, health-first tone.",
                "expresses_concern": True,
                "recommends_medical_advice": True,
                "offers_plan_modification": True,
                "suggests_alternatives": True,
                "asks_about_severity": True,
                "tone": "cautious, health-first, supportive",
                "addresses_safety": True
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "coach_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "coaching_eval_v1",
                    "safety_review": "approved"
                }
            },
            "tags": {
                "agent": "conversation_agent",
                "mode": "coaching",
                "interaction_type": "plan_modification",
                "safety_critical": "true",
                "injury_related": "true",
                "priority": "critical"
            }
        }
    ]
}


# Meal Phase Agent Dataset
meal_phase_dataset = {
    "name": "meal_phase_simple_v1",
    "version": "1.0.0",
    "description": "Meal phase agent evaluation - phase-specific nutrition planning",
    "test_cases": [
        {
            "id": "mp_001",
            "inputs": {
                "meal_plan_description": "Mediterranean-style nutrition plan for muscle building with emphasis on whole foods",
                "phase_number": 1,
                "phase_name": "Foundation Phase",
                "phase_objectives": ["Establish baseline calories", "Build healthy eating habits", "Assess metabolic response"],
                "phase_duration_weeks": 4,
                "phase_start_date": "2025-12-15",
                "phase_start_day": "Sunday",
                "dietary_restrictions": ["No dairy", "Pescatarian"],
                "meal_frequency": 4
            },
            "expectations": {
                "expected_behavior": "Generate phase-specific meal plan with 4 meals/day for pescatarian with no dairy. Foundation phase should have baseline calories (2500-2800). Include 2 sample days (training + rest). Must include grocery list with categories and shopping schedule. Must include meal prep sessions with instructions and prep schedule. All schedules use target_day_name format.",
                "calorie_range": "2500-2800",
                "macro_split_appropriate": True,
                "sample_days_count": 2,
                "meals_per_day": 4,
                "honors_dietary_restrictions": True,
                "includes_grocery_list": True,
                "includes_shopping_schedule": True,
                "includes_prep_sessions": True,
                "includes_prep_schedule": True,
                "schedule_uses_day_names": True
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "nutrition_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "meal_agent_eval_v1"
                }
            },
            "tags": {
                "agent": "meal_phase_agent",
                "diet_type": "pescatarian",
                "dietary_restrictions": "no_dairy",
                "phase": "foundation",
                "priority": "high"
            }
        },
        {
            "id": "mp_002",
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
                "expected_behavior": "Generate hypertrophy phase meal plan with 5 meals/day. Should have calorie surplus (3000-3400). High protein (35-40%). Include pre/post workout nutrition. Must include complete grocery shopping and meal prep schedules with explicit day names and repeat patterns.",
                "calorie_range": "3000-3400",
                "protein_percentage": "35-40",
                "sample_days_count": 2,
                "meals_per_day": 5,
                "includes_preworkout_meal": True,
                "includes_postworkout_meal": True,
                "includes_shopping_schedule": True,
                "includes_prep_schedule": True,
                "schedule_format": "day_name_with_repeats"
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "nutrition_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "meal_agent_eval_v1"
                }
            },
            "tags": {
                "agent": "meal_phase_agent",
                "diet_type": "omnivore",
                "phase": "hypertrophy",
                "goal": "muscle_growth",
                "priority": "high"
            }
        }
    ]
}


def save_datasets():
    """Save datasets to JSON files."""
# Query Agent Dataset
query_agent_dataset = {
    "name": "query_agent_simple_v1",
    "version": "1.0.0",
    "description": "Query agent database query evaluation",
    "test_cases": [
        {
            "id": "query_001",
            "inputs": {
                "user_id": "c2608a59-3af8-4600-9de3-3ce004d40187",  # eval_test_user@fitness.ai
                "query_request": "Get my current active fitness plan with all workout and meal details"
            },
            "expectations": {
                "expected_behavior": "Execute SQL query to retrieve active fitness plan with phases, workout_plan metadata, and meal_plan metadata. Use correct column names (daily_calorie_target, protein_grams_target, etc.). Return structured results with plan info, workout frequency, progression strategy, calorie targets, and macro targets.",
                "uses_correct_columns": True,
                "includes_workout_plan": True,
                "includes_meal_plan": True,
                "uses_mcp_tools": True,
                "returns_structured_data": True,
                "query_efficiency": "good"
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "database_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "query_agent_eval_v1"
                }
            },
            "tags": {
                "query_type": "complex_join",
                "priority": "high",
                "complexity": "medium"
            }
        },
        {
            "id": "query_002",
            "inputs": {
                "user_id": "c2608a59-3af8-4600-9de3-3ce004d40187",
                "query_request": "What are my daily calorie and protein targets from my meal plan?"
            },
            "expectations": {
                "expected_behavior": "Execute SQL query to get meal_plan data with CORRECT column names: daily_calorie_target, protein_grams_target. Return simple, clear answer with numeric values. Must NOT use incorrect column names like 'daily_calories' or 'protein_g'.",
                "uses_correct_column_names": True,
                "includes_calorie_target": True,
                "includes_protein_target": True,
                "query_simplicity": "simple",
                "returns_numeric_values": True
            },
            "source": {
                "source_type": "HUMAN",
                "source_data": {
                    "curator": "database_expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "guidelines": "query_agent_eval_v1"
                }
            },
            "tags": {
                "query_type": "simple_select",
                "priority": "critical",
                "complexity": "low",
                "schema_accuracy_test": "true"
            }
        }
    ]
}


def save_datasets():
    """Save all datasets to JSON files."""
    datasets_dir = Path(__file__).parent / "datasets_simple"
    datasets_dir.mkdir(exist_ok=True)
    
    datasets = [
        (workout_phase_dataset, "workout_phase_simple_v1.json"),
        (intake_dataset, "intake_simple_v1.json"),
        (coach_dataset, "fitness_coach_simple_v1.json"),
        (meal_phase_dataset, "meal_phase_simple_v1.json"),
        (query_agent_dataset, "query_agent_simple_v1.json")
    ]
    
    for dataset, filename in datasets:
        filepath = datasets_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved {filename} (v{dataset['version']})")
    
    print(f"\n[OK] Datasets saved to {datasets_dir}")
    print("[OK] Format: MLflow 3.7.0 compatible (flat expectations dict)")


if __name__ == "__main__":
    save_datasets()
