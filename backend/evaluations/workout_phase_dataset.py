"""Evaluation test cases for the workout phase generation agent.

This dataset tests the agent's ability to generate appropriate workout phases
based on user requirements, fitness level, and equipment availability.
"""
from evaluations.dataset_schema import WorkoutPhaseTestCase, EvaluationDataset


# Test Case 1: Beginner Full Body - Foundation Phase
tc1 = WorkoutPhaseTestCase(
    id="workout_phase_001",
    description="Beginner with gym access - Foundation phase (adaptation)",
    input={
        "phase_name": "Foundation",
        "phase_number": 1,
        "duration_weeks": 4,
        "objectives": [
            "Build foundational strength",
            "Learn proper exercise form",
            "Establish consistent training habit"
        ],
        "user_profile": {
            "fitness_level": "beginner",
            "equipment": "full_gym",
            "experience_years": 0,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 3,
            "duration_minutes": 45,
            "preferred_days": ["Monday", "Wednesday", "Friday"]
        }
    },
    expected_output={
        "workout_count": 3,
        "workout_types": ["strength", "strength", "strength"],
        "intensity_levels": ["low", "low", "low"],
        "exercises_per_workout": {"workout_1": 6, "workout_2": 6, "workout_3": 6},
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "compound_exercise_focus": True
    },
    metadata={
        "category": "beginner",
        "program_type": "full_body",
        "expected_difficulty": "low"
    }
)

# Test Case 2: Intermediate Upper/Lower - Strength Building Phase
tc2 = WorkoutPhaseTestCase(
    id="workout_phase_002",
    description="Intermediate with gym access - Strength building phase",
    input={
        "phase_name": "Strength Development",
        "phase_number": 2,
        "duration_weeks": 6,
        "objectives": [
            "Increase compound lift strength",
            "Build muscle mass",
            "Improve work capacity"
        ],
        "user_profile": {
            "fitness_level": "intermediate",
            "equipment": "full_gym",
            "experience_years": 2,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 4,
            "duration_minutes": 60,
            "preferred_days": ["Monday", "Tuesday", "Thursday", "Friday"]
        }
    },
    expected_output={
        "workout_count": 4,
        "workout_types": ["strength", "strength", "strength", "strength"],
        "intensity_levels": ["moderate", "moderate", "moderate", "moderate"],
        "exercises_per_workout": {"workout_1": 7, "workout_2": 7, "workout_3": 7, "workout_4": 7},
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "upper_lower_split": True
    },
    metadata={
        "category": "intermediate",
        "program_type": "upper_lower",
        "expected_difficulty": "moderate"
    }
)

# Test Case 3: Advanced PPL - Hypertrophy Focus
tc3 = WorkoutPhaseTestCase(
    id="workout_phase_003",
    description="Advanced with gym access - Hypertrophy phase (PPL split)",
    input={
        "phase_name": "Hypertrophy Focus",
        "phase_number": 2,
        "duration_weeks": 8,
        "objectives": [
            "Maximize muscle growth",
            "Increase training volume",
            "Refine mind-muscle connection"
        ],
        "user_profile": {
            "fitness_level": "advanced",
            "equipment": "full_gym",
            "experience_years": 5,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 6,
            "duration_minutes": 75,
            "preferred_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        }
    },
    expected_output={
        "workout_count": 6,
        "workout_types": ["strength", "strength", "strength", "strength", "strength", "strength"],
        "intensity_levels": ["high", "high", "high", "high", "high", "high"],
        "exercises_per_workout": {
            "workout_1": 8, "workout_2": 8, "workout_3": 8,
            "workout_4": 8, "workout_5": 8, "workout_6": 8
        },
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "ppl_split": True
    },
    metadata={
        "category": "advanced",
        "program_type": "ppl",
        "expected_difficulty": "high"
    }
)

# Test Case 4: Beginner Home Workout - Limited Equipment
tc4 = WorkoutPhaseTestCase(
    id="workout_phase_004",
    description="Beginner with home equipment (dumbbells only) - Adaptation phase",
    input={
        "phase_name": "Home Training Adaptation",
        "phase_number": 1,
        "duration_weeks": 4,
        "objectives": [
            "Build base strength with limited equipment",
            "Master bodyweight movements",
            "Develop training consistency"
        ],
        "user_profile": {
            "fitness_level": "beginner",
            "equipment": "dumbbells",
            "experience_years": 0,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 3,
            "duration_minutes": 30,
            "preferred_days": ["Monday", "Wednesday", "Friday"]
        }
    },
    expected_output={
        "workout_count": 3,
        "workout_types": ["strength", "strength", "strength"],
        "intensity_levels": ["low", "low", "low"],
        "exercises_per_workout": {"workout_1": 5, "workout_2": 5, "workout_3": 5},
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "uses_only_dumbbells_bodyweight": True
    },
    metadata={
        "category": "beginner",
        "program_type": "full_body",
        "expected_difficulty": "low",
        "equipment_constraint": "limited"
    }
)

# Test Case 5: Fat Loss with Cardio Integration
tc5 = WorkoutPhaseTestCase(
    id="workout_phase_005",
    description="Intermediate fat loss phase with cardio integration",
    input={
        "phase_name": "Fat Loss Acceleration",
        "phase_number": 2,
        "duration_weeks": 6,
        "objectives": [
            "Maximize calorie burn",
            "Preserve muscle mass",
            "Improve cardiovascular fitness"
        ],
        "user_profile": {
            "fitness_level": "intermediate",
            "equipment": "full_gym",
            "experience_years": 1.5,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 5,
            "duration_minutes": 50,
            "preferred_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"]
        }
    },
    expected_output={
        "workout_count": 5,
        "workout_types": ["strength", "hybrid", "strength", "cardio", "hybrid"],
        "intensity_levels": ["moderate", "moderate", "moderate", "moderate", "moderate"],
        "exercises_per_workout": {
            "workout_1": 7, "workout_2": 6, "workout_3": 7,
            "workout_4": 5, "workout_5": 6
        },
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "includes_cardio": True
    },
    metadata={
        "category": "intermediate",
        "program_type": "hybrid",
        "expected_difficulty": "moderate",
        "goal": "fat_loss"
    }
)

# Test Case 6: Injury Modification - Lower Back Issues
tc6 = WorkoutPhaseTestCase(
    id="workout_phase_006",
    description="Intermediate with lower back injury - Safe progression phase",
    input={
        "phase_name": "Rehabilitation and Strength",
        "phase_number": 1,
        "duration_weeks": 4,
        "objectives": [
            "Rebuild strength safely",
            "Avoid aggravating lower back",
            "Strengthen core and stabilizers"
        ],
        "user_profile": {
            "fitness_level": "intermediate",
            "equipment": "full_gym",
            "experience_years": 2,
            "injuries": ["lower_back_strain"]
        },
        "workout_preferences": {
            "frequency_per_week": 3,
            "duration_minutes": 45,
            "preferred_days": ["Monday", "Wednesday", "Friday"]
        }
    },
    expected_output={
        "workout_count": 3,
        "workout_types": ["strength", "strength", "strength"],
        "intensity_levels": ["low", "low", "low"],
        "exercises_per_workout": {"workout_1": 6, "workout_2": 6, "workout_3": 6},
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "avoids_spinal_loading": True,
        "includes_core_work": True
    },
    metadata={
        "category": "injury_modification",
        "program_type": "full_body",
        "expected_difficulty": "low",
        "safety_focus": "lower_back"
    }
)

# Test Case 7: Time-Constrained Professional
tc7 = WorkoutPhaseTestCase(
    id="workout_phase_007",
    description="Intermediate professional with only 30 min per workout",
    input={
        "phase_name": "Efficient Strength",
        "phase_number": 1,
        "duration_weeks": 6,
        "objectives": [
            "Build strength efficiently",
            "Maximize time efficiency",
            "Focus on compound movements"
        ],
        "user_profile": {
            "fitness_level": "intermediate",
            "equipment": "full_gym",
            "experience_years": 3,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 3,
            "duration_minutes": 30,
            "preferred_days": ["Monday", "Wednesday", "Friday"]
        }
    },
    expected_output={
        "workout_count": 3,
        "workout_types": ["strength", "strength", "strength"],
        "intensity_levels": ["moderate", "moderate", "moderate"],
        "exercises_per_workout": {"workout_1": 4, "workout_2": 4, "workout_3": 4},
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "compound_focus": True,
        "minimal_isolation": True
    },
    metadata={
        "category": "time_constrained",
        "program_type": "full_body",
        "expected_difficulty": "moderate",
        "constraint": "time"
    }
)

# Test Case 8: Bodyweight Only - No Equipment
tc8 = WorkoutPhaseTestCase(
    id="workout_phase_008",
    description="Intermediate with no equipment - Bodyweight strength phase",
    input={
        "phase_name": "Bodyweight Mastery",
        "phase_number": 2,
        "duration_weeks": 6,
        "objectives": [
            "Progress to advanced bodyweight skills",
            "Increase relative strength",
            "Master movement patterns"
        ],
        "user_profile": {
            "fitness_level": "intermediate",
            "equipment": "bodyweight_only",
            "experience_years": 2,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 4,
            "duration_minutes": 45,
            "preferred_days": ["Monday", "Tuesday", "Thursday", "Saturday"]
        }
    },
    expected_output={
        "workout_count": 4,
        "workout_types": ["strength", "strength", "strength", "strength"],
        "intensity_levels": ["moderate", "moderate", "moderate", "moderate"],
        "exercises_per_workout": {"workout_1": 6, "workout_2": 6, "workout_3": 6, "workout_4": 6},
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "bodyweight_only": True,
        "includes_progressions": True
    },
    metadata={
        "category": "bodyweight",
        "program_type": "upper_lower",
        "expected_difficulty": "moderate",
        "equipment_constraint": "none"
    }
)

# Test Case 9: High Frequency Training - Advanced
tc9 = WorkoutPhaseTestCase(
    id="workout_phase_009",
    description="Advanced athlete - High frequency strength phase (5 days)",
    input={
        "phase_name": "Strength Peaking",
        "phase_number": 3,
        "duration_weeks": 4,
        "objectives": [
            "Peak strength for competition",
            "Maintain muscle mass",
            "Optimize recovery between sessions"
        ],
        "user_profile": {
            "fitness_level": "advanced",
            "equipment": "full_gym",
            "experience_years": 7,
            "injuries": []
        },
        "workout_preferences": {
            "frequency_per_week": 5,
            "duration_minutes": 90,
            "preferred_days": ["Monday", "Tuesday", "Thursday", "Friday", "Saturday"]
        }
    },
    expected_output={
        "workout_count": 5,
        "workout_types": ["strength", "strength", "strength", "strength", "strength"],
        "intensity_levels": ["high", "high", "high", "high", "moderate"],
        "exercises_per_workout": {
            "workout_1": 6, "workout_2": 6, "workout_3": 6,
            "workout_4": 6, "workout_5": 5
        },
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "competition_focused": True,
        "includes_deload_session": True
    },
    metadata={
        "category": "advanced",
        "program_type": "powerlifting",
        "expected_difficulty": "high",
        "goal": "strength_peaking"
    }
)

# Test Case 10: Senior Fitness - Joint-Friendly
tc10 = WorkoutPhaseTestCase(
    id="workout_phase_010",
    description="Older adult (60+) - Joint-friendly strength maintenance",
    input={
        "phase_name": "Healthy Aging Strength",
        "phase_number": 1,
        "duration_weeks": 8,
        "objectives": [
            "Maintain functional strength",
            "Improve balance and stability",
            "Support joint health"
        ],
        "user_profile": {
            "fitness_level": "beginner",
            "equipment": "dumbbells",
            "experience_years": 0,
            "injuries": ["arthritis_knees"],
            "age": 62
        },
        "workout_preferences": {
            "frequency_per_week": 2,
            "duration_minutes": 30,
            "preferred_days": ["Tuesday", "Friday"]
        }
    },
    expected_output={
        "workout_count": 2,
        "workout_types": ["strength", "strength"],
        "intensity_levels": ["low", "low"],
        "exercises_per_workout": {"workout_1": 5, "workout_2": 5},
        "equipment_match": True,
        "duration_match": True,
        "has_warmup": True,
        "has_cooldown": True,
        "joint_friendly": True,
        "includes_balance_work": True,
        "functional_focus": True
    },
    metadata={
        "category": "senior",
        "program_type": "full_body",
        "expected_difficulty": "low",
        "safety_focus": "joints",
        "age_group": "senior"
    }
)


# Create the dataset
workout_phase_dataset = EvaluationDataset(
    name="workout_phase_generation_v1",
    version="1.0.0",
    description="Evaluation dataset for workout phase generation agent covering beginner to advanced scenarios with various constraints",
    agent_name="workout_phase_agent",
    test_cases=[tc1, tc2, tc3, tc4, tc5, tc6, tc7, tc8, tc9, tc10]
)


if __name__ == "__main__":
    # Save dataset to JSON
    import json
    from pathlib import Path
    
    output_dir = Path(__file__).parent / "datasets"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "workout_phase_generation_v1.json"
    with open(output_file, "w") as f:
        json.dump(workout_phase_dataset.to_mlflow_format(), f, indent=2)
    
    print(f"✓ Created dataset with {len(workout_phase_dataset.test_cases)} test cases")
    print(f"✓ Saved to {output_file}")
