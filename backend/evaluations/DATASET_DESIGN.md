# Evaluation Dataset Design

## Overview

Created simple evaluation datasets for three agent types, matching their actual input/output schemas for LLM-as-a-judge evaluation.

## Key Design Principles

### 1. **Inputs Match Agent Expectations**
- **Workout Phase Agent**: Receives phase context (name, objectives, duration, fitness level, equipment)
- **Intake Agent**: Receives chat history (list of messages)
- **Fitness Coach Agent**: Receives chat history + user context (active plan, current phase)

### 2. **Expectations for LLM Judges**
Each test case has three types of expectations:

#### `expected_behavior` (string)
Natural language description of what the agent should do. This is the primary input for LLM-as-a-judge.

**Example:**
```json
"expected_behavior": "Agent should generate 3 distinct full-body workouts focusing on fundamental compound movements (squat, deadlift, bench press, rows, overhead press). Each workout should have 6-8 exercises with beginner-appropriate volume (3 sets x 8-12 reps). The workout_cycle should be 3 training days + 4 rest days. Intensity should be moderate (RPE 6-7), volume should be low-moderate for adaptation, and progression should be linear (add weight weekly)."
```

#### `expected_structure` (object)
Describes the expected output structure, matching the agent's `output_type` Pydantic model.

**Example:**
```json
"expected_structure": {
  "workouts": {
    "count": 3,
    "type": "Each workout should be a WorkoutDay with exercises array"
  },
  "workout_cycle": {
    "length": 7,
    "pattern": "3 workout days, 4 rest days"
  },
  "intensity_guidance": "Should mention RPE 6-7 or light-moderate intensity",
  "volume_notes": "Should specify low-moderate volume for adaptation",
  "progression_notes": "Should specify linear progression"
}
```

#### `validation_criteria` (object)
Automated checks for deterministic validation.

**Example:**
```json
"validation_criteria": {
  "workout_count": 3,
  "exercises_per_workout_min": 6,
  "exercises_per_workout_max": 8,
  "has_compound_movements": true,
  "appropriate_for_beginner": true
}
```

## Agent-Specific Schemas

### Workout Phase Agent
**Input Type:** Phase context (dict)
```json
{
  "workout_plan_description": "string",
  "phase_number": 1,
  "phase_name": "string",
  "phase_objectives": ["string"],
  "phase_duration_weeks": 4,
  "fitness_level": "beginner|intermediate|advanced",
  "equipment_access": ["string"],
  "workout_frequency": 3
}
```

**Output Type:** `PhaseWorkoutDetails`
- `workouts`: list[WorkoutDay]
- `workout_cycle`: list[WorkoutCycleItem]
- `intensity_guidance`: str
- `volume_notes`: str
- `progression_notes`: str

### Intake Agent
**Input Type:** Chat history
```json
{
  "messages": [
    {
      "role": "user",
      "content": "string"
    }
  ]
}
```

**Output Type:** Conversational response (string)
- Should ask clarifying questions
- Should acknowledge user input
- Should build toward plan creation

### Fitness Coach Agent
**Input Type:** Chat history + context
```json
{
  "messages": [
    {
      "role": "user",
      "content": "string"
    }
  ],
  "user_context": {
    "has_active_plan": true,
    "plan_name": "string",
    "current_phase": "string",
    "current_week": 2
  }
}
```

**Output Type:** Conversational response OR tool use
- May use `query_agent` for database queries
- May use modification tools
- Should provide clear, helpful responses

## Dataset Files

### Simple Datasets (Current)
- `workout_phase_simple_v1.json` - 2 test cases
- `intake_simple_v1.json` - 2 test cases
- `fitness_coach_simple_v1.json` - 2 test cases

Location: `backend/evaluations/datasets_simple/`

### Full Datasets (Legacy)
- `workout_phase_generation_v1.json` - 10 test cases (older format)

Location: `backend/evaluations/datasets/`

## Usage with MLflow

To upload a dataset:
```python
from mlflow.genai.datasets import create_dataset

# Transform test cases to MLflow format
mlflow_records = [
    {
        "inputs": test_case["inputs"],
        "expectations": test_case["expectations"],
        "metadata": test_case["metadata"]
    }
    for test_case in dataset["test_cases"]
]

# Create and populate dataset
dataset = create_dataset(
    name="workout_phase_simple_v1",
    experiment_id=["1"],
    tags={"version": "1.0.0", "agent": "workout_phase_agent"}
)
dataset.merge_records(mlflow_records)
```

## Next Steps

1. **Upload simple datasets to MLflow** - Test with current 2-case datasets
2. **Build agent runner** - Wrapper to execute agents and collect outputs
3. **Configure LLM judges** - Use `expected_behavior` as ground truth
4. **Run evaluation** - Execute `mlflow.genai.evaluate()`
5. **Expand datasets** - Add more test cases once evaluation flow works

## Why This Structure Works

1. **LLM judges can understand natural language expectations** - `expected_behavior` provides clear context
2. **Automated validation still possible** - `validation_criteria` enables deterministic checks
3. **Structure hints guide judges** - `expected_structure` helps LLM understand what "good" looks like
4. **Inputs match reality** - Agent evaluation reflects actual production usage
5. **Extensible** - Easy to add more test cases in the same format
