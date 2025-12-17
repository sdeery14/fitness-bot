"""Simplified evaluation datasets matching agent input/output schemas.

For each agent, inputs match what the agent actually receives,
and expectations match the agent's output_type (Pydantic model).
"""

import json
from pathlib import Path


# ============================================================================
# 1. WORKOUT PHASE AGENT DATASET
# ============================================================================
# Agent: workout_phase_agent
# Input: phase context + workout plan description
# Output: PhaseWorkoutDetails (workouts, workout_cycle, intensity_guidance, volume_notes, progression_notes)

workout_phase_simple = {
    "name": "workout_phase_simple_v1",
    "version": "1.0.0",
    "description": "Simple evaluation dataset for workout phase generation agent",
    "test_cases": [
        {
            "id": "wp_simple_001",
            "description": "Beginner foundation phase - 3x/week full body",
            "inputs": {
                # This is what the workout_phase_agent actually receives
                "workout_plan_description": "3-day per week full-body strength training program for a beginner. Focus on compound movements and proper form development.",
                "phase_number": 1,
                "phase_name": "Foundation Phase",
                "phase_objectives": [
                    "Build foundational strength",
                    "Learn proper exercise form",
                    "Establish consistent training habit"
                ],
                "phase_duration_weeks": 4,
                "fitness_level": "beginner",
                "equipment_access": ["barbell", "dumbbells", "bench", "squat_rack"],
                "workout_frequency": 3
            },
            "expectations": {
                # What behavior we expect from the agent
                "expected_behavior": "Agent should generate 3 distinct full-body workouts focusing on fundamental compound movements (squat, deadlift, bench press, rows, overhead press). Each workout should have 6-8 exercises with beginner-appropriate volume (3 sets x 8-12 reps). The workout_cycle should be 3 training days + 4 rest days. Intensity should be moderate (RPE 6-7), volume should be low-moderate for adaptation, and progression should be linear (add weight weekly).",
                
                # Expected structure (matches PhaseWorkoutDetails schema)
                "expected_structure": {
                    "workouts": {
                        "count": 3,
                        "type": "Each workout should be a WorkoutDay with exercises array"
                    },
                    "workout_cycle": {
                        "length": 7,
                        "pattern": "3 workout days, 4 rest days"
                    },
                    "intensity_guidance": "Should mention RPE 6-7 or light-moderate intensity for beginners",
                    "volume_notes": "Should specify low-moderate volume appropriate for adaptation (e.g., '10-12 sets per muscle group per week')",
                    "progression_notes": "Should specify linear progression (e.g., 'Add 5 lbs per week when completing all sets')"
                },
                
                # Validation criteria (automated checks)
                "validation_criteria": {
                    "workout_count": 3,
                    "exercises_per_workout_min": 6,
                    "exercises_per_workout_max": 8,
                    "has_compound_movements": True,
                    "appropriate_for_beginner": True
                }
            },
            "metadata": {
                "agent": "workout_phase_agent",
                "fitness_level": "beginner",
                "test_type": "basic_functionality"
            }
        },
        {
            "id": "wp_simple_002",
            "description": "Intermediate hypertrophy phase - 4x/week upper/lower split",
            "inputs": {
                "workout_plan_description": "4-day upper/lower split focused on muscle growth with moderate-high volume.",
                "phase_number": 2,
                "phase_name": "Hypertrophy Phase",
                "phase_objectives": [
                    "Maximize muscle growth",
                    "Increase training volume",
                    "Refine mind-muscle connection"
                ],
                "phase_duration_weeks": 8,
                "fitness_level": "intermediate",
                "equipment_access": ["full_gym"],
                "workout_frequency": 4
            },
            "expectations": {
                "expected_behavior": "Agent should generate 4 distinct workouts (2 upper body, 2 lower body) with hypertrophy-focused training. Upper workouts should have 8-10 exercises targeting chest, back, shoulders, arms. Lower workouts should have 7-9 exercises targeting quads, hamstrings, glutes, calves. Volume should be moderate-high (3-4 sets x 8-12 reps). The workout_cycle should alternate upper/lower with rest days. Intensity should be RPE 7-8, volume should be 16-20 sets per muscle per week, and progression should focus on adding reps before weight.",
                
                "expected_structure": {
                    "workouts": {
                        "count": 4,
                        "pattern": "2 upper body, 2 lower body workouts"
                    },
                    "workout_cycle": {
                        "length": 7,
                        "pattern": "upper, lower, rest, upper, lower, rest, rest"
                    },
                    "intensity_guidance": "Should mention RPE 7-8 or moderate-high intensity",
                    "volume_notes": "Should specify moderate-high volume for hypertrophy (e.g., '16-20 sets per muscle group per week')",
                    "progression_notes": "Should emphasize progressive overload via reps then weight"
                },
                
                "validation_criteria": {
                    "workout_count": 4,
                    "upper_lower_split": True,
                    "hypertrophy_rep_range": True,  # 8-12 reps
                    "appropriate_volume": True
                }
            },
            "metadata": {
                "agent": "workout_phase_agent",
                "fitness_level": "intermediate",
                "test_type": "split_routine"
            }
        }
    ]
}


# ============================================================================
# 2. INTAKE AGENT DATASET
# ============================================================================
# Agent: conversation_agent (intake mode)
# Input: chat history (list of messages)
# Output: Conversational response + potentially triggers fitness plan creation

intake_simple = {
    "name": "intake_simple_v1",
    "version": "1.0.0",
    "description": "Simple evaluation dataset for intake/onboarding conversation agent",
    "test_cases": [
        {
            "id": "intake_simple_001",
            "description": "New user starting fitness journey - complete intake",
            "inputs": {
                # Chat history format - what the agent receives
                "messages": [
                    {
                        "role": "user",
                        "content": "Hi, I want to get in shape. I've never really worked out before but I have access to a gym."
                    }
                ]
            },
            "expectations": {
                "expected_behavior": "Agent should warmly welcome the user, acknowledge their beginner status and gym access. Should ask clarifying questions about their specific goal (lose weight, build muscle, general fitness), current activity level, any injuries or limitations, and time availability. The agent should be encouraging and not overwhelming. Response should be conversational and ask 1-2 questions at a time.",
                
                "expected_response_characteristics": {
                    "tone": "warm, encouraging, professional",
                    "asks_about": ["specific fitness goal", "current activity level", "injuries or limitations", "time availability"],
                    "question_count": "1-2 questions (not overwhelming)",
                    "acknowledges_user_input": True
                },
                
                "validation_criteria": {
                    "is_conversational": True,
                    "asks_questions": True,
                    "appropriate_for_beginner": True,
                    "does_not_create_plan_yet": True  # Should gather more info first
                }
            },
            "metadata": {
                "agent": "conversation_agent",
                "mode": "intake",
                "test_type": "initial_contact"
            }
        },
        {
            "id": "intake_simple_002",
            "description": "User provides complete info - ready to build plan",
            "inputs": {
                "messages": [
                    {
                        "role": "user",
                        "content": "I want to build muscle. I'm 28, never lifted before, and I can train 4 days a week for about an hour each session. I have access to a full gym. No injuries."
                    }
                ]
            },
            "expectations": {
                "expected_behavior": "Agent should recognize this is comprehensive information and could proceed with plan creation. Should summarize what they heard (muscle building, beginner, 4x/week, 1 hour sessions, full gym, no injuries) and ask if the user is ready to create their plan, or if there are any other preferences (preferred training days, dietary restrictions, etc.). Tone should be positive and action-oriented.",
                
                "expected_response_characteristics": {
                    "summarizes_user_info": True,
                    "ready_to_proceed": True,
                    "asks_confirmation": True,
                    "tone": "positive, action-oriented"
                },
                
                "validation_criteria": {
                    "acknowledges_all_info": True,
                    "offers_to_create_plan": True,
                    "asks_for_confirmation": True
                }
            },
            "metadata": {
                "agent": "conversation_agent",
                "mode": "intake",
                "test_type": "complete_info_provided"
            }
        }
    ]
}


# ============================================================================
# 3. FITNESS COACH AGENT DATASET
# ============================================================================
# Agent: conversation_agent (coaching mode)
# Input: chat history + existing plan context
# Output: Conversational response OR tool use (query/modify plan)

fitness_coach_simple = {
    "name": "fitness_coach_simple_v1",
    "version": "1.0.0",
    "description": "Simple evaluation dataset for fitness coach conversation agent",
    "test_cases": [
        {
            "id": "coach_simple_001",
            "description": "User asks about their current workout plan",
            "inputs": {
                "messages": [
                    {
                        "role": "user",
                        "content": "What workouts do I have this week?"
                    }
                ],
                "user_context": {
                    "has_active_plan": True,
                    "plan_name": "12-Week Muscle Building Program",
                    "current_phase": "Foundation Phase",
                    "current_week": 2
                }
            },
            "expectations": {
                "expected_behavior": "Agent should use the query_agent (database query) to retrieve the user's workout schedule for the current week. Should present the information clearly and ask if the user wants more details about any specific workout. Should be encouraging and supportive.",
                
                "expected_tool_use": {
                    "uses_query_agent": True,
                    "query_type": "workout_schedule",
                    "query_scope": "current_week"
                },
                
                "expected_response_characteristics": {
                    "presents_workout_schedule": True,
                    "offers_more_details": True,
                    "tone": "encouraging, supportive"
                },
                
                "validation_criteria": {
                    "uses_correct_tool": True,
                    "provides_clear_answer": True,
                    "offers_follow_up": True
                }
            },
            "metadata": {
                "agent": "conversation_agent",
                "mode": "coaching",
                "test_type": "plan_query"
            }
        },
        {
            "id": "coach_simple_002",
            "description": "User wants to adjust their plan due to injury",
            "inputs": {
                "messages": [
                    {
                        "role": "user",
                        "content": "I hurt my shoulder doing overhead press yesterday. Can we modify my workouts to avoid shoulder pain?"
                    }
                ],
                "user_context": {
                    "has_active_plan": True,
                    "plan_name": "Upper/Lower Split",
                    "current_phase": "Building Phase"
                }
            },
            "expectations": {
                "expected_behavior": "Agent should express concern about the injury and recommend seeing a healthcare provider if pain is severe. Should offer to temporarily modify the plan to avoid overhead pressing movements and replace them with shoulder-friendly alternatives. Should ask about pain severity and range of motion. Tone should be cautious and health-first.",
                
                "expected_response_characteristics": {
                    "expresses_concern": True,
                    "recommends_medical_advice_if_needed": True,
                    "offers_plan_modification": True,
                    "suggests_alternatives": True,
                    "asks_clarifying_questions": True,
                    "tone": "cautious, health-first, supportive"
                },
                
                "validation_criteria": {
                    "addresses_safety": True,
                    "offers_solution": True,
                    "asks_about_severity": True
                }
            },
            "metadata": {
                "agent": "conversation_agent",
                "mode": "coaching",
                "test_type": "plan_modification_injury"
            }
        }
    ]
}


# ============================================================================
# SAVE DATASETS
# ============================================================================

def save_datasets():
    """Save all simple datasets to JSON files."""
    datasets_dir = Path(__file__).parent / "datasets_simple"
    datasets_dir.mkdir(exist_ok=True)
    
    datasets = [
        (workout_phase_simple, "workout_phase_simple_v1.json"),
        (intake_simple, "intake_simple_v1.json"),
        (fitness_coach_simple, "fitness_coach_simple_v1.json")
    ]
    
    for dataset, filename in datasets:
        filepath = datasets_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {filename}")
    
    print(f"\n✓ All datasets saved to {datasets_dir}")


if __name__ == "__main__":
    save_datasets()
