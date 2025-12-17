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


def save_datasets():
    """Save datasets to JSON files."""
    datasets_dir = Path(__file__).parent / "datasets_simple"
    datasets_dir.mkdir(exist_ok=True)
    
    datasets = [
        (workout_phase_dataset, "workout_phase_simple_v1.json"),
        (intake_dataset, "intake_simple_v1.json"),
        (coach_dataset, "fitness_coach_simple_v1.json")
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
