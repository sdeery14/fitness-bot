# Fitness Plan Schema Migration Summary

## Overview
Migrated from single-phase generic plans to temporally-aware multi-phase plans with separated metadata and phase-specific details.

## Schema Changes

### Old Structure
```json
{
  "workout_plan_output": {
    "workout_plan": {
      "program_type": "...",
      "frequency_per_week": 4,
      "duration_weeks": 12,
      "training_cycle": [...],
      "workouts": [...]
    }
  },
  "meal_plan_output": {
    "meal_plan": {
      "daily_calorie_target": 2000,
      "macro_split": "...",
      "sample_days": [...]
    }
  }
}
```

### New Structure
```json
{
  "workout_metadata": {
    "program_type": "...",
    "progression_strategy": "...",
    "training_principles": [...],
    "equipment_used": [...],
    "phase_progression_notes": "..."
  },
  "meal_metadata": {
    "dietary_approach": "...",
    "macro_strategy": "...",
    "meal_timing": "...",
    "hydration_guidance": "...",
    "phase_nutrition_notes": "..."
  },
  "phases": [
    {
      "phase_number": 1,
      "name": "Foundation Phase",
      "objectives": [...],
      "duration_weeks": 4,
      "start_date": "2024-01-01",
      "end_date": "2024-01-28",
      "workout_details": {
        "workout_cycle": [...],
        "intensity_guidance": "...",
        "volume_notes": "...",
        "progression_notes": "..."
      },
      "meal_details": {
        "daily_calorie_target": 2000,
        "macro_split": "40/30/30",
        "sample_days": [...],
        "phase_nutrition_focus": "..."
      }
    }
  ]
}
```

## Key Architectural Changes

### 1. Temporal Awareness
- **Added Fields**: `start_date`, `end_date` to `FitnessPlanInput` and `PhaseOutput`
- **Purpose**: Enable precise scheduling based on actual dates rather than generic weeks
- **Implementation**: Phases calculate their dates sequentially based on duration_weeks

### 2. Required Multi-Phase Plans
- **Changed**: `phases` field from optional to required (min_length=1)
- **Purpose**: Force AI to always create structured, progressive plans
- **Guidance**: Updated conversation_agent prompts to emphasize phase creation

### 3. Metadata Separation
- **Created Models**: 
  - `WorkoutPlanMetadata` - Plan-level workout strategy
  - `MealPlanMetadata` - Plan-level nutrition strategy
  - `PhaseWorkoutDetails` - Phase-specific workout implementation
  - `PhaseMealDetails` - Phase-specific meal implementation
- **Purpose**: Eliminate redundancy, metadata defined once by conversation agent
- **Benefit**: Phase agents only generate phase-specific details

### 4. Specialized Phase Agents
- **Created Agents**:
  - `workout_phase_agent` - Generates PhaseWorkoutDetails
  - `meal_phase_agent` - Generates PhaseMealDetails
- **Purpose**: Separation of concerns, each agent focused on specific phase details
- **Flow**: conversation_agent → build_fitness_plan → workout_phase_agent + meal_phase_agent (per phase)

## Files Modified

### Backend - AI Schema Layer
- **backend/src/ai/schemas.py**
  - Added metadata models (WorkoutPlanMetadata, MealPlanMetadata)
  - Added phase detail models (PhaseWorkoutDetails, PhaseMealDetails)
  - Updated PhaseOutput: workout_plan_output → workout_details, meal_plan_output → meal_details
  - Updated FitnessPlanOutput: added workout_metadata, meal_metadata
  - Updated validate_completeness() to reference new fields

### Backend - AI Tools Layer
- **backend/src/ai/tools/plan_tools.py**
  - Added start_date, end_date to FitnessPlanInput
  - Made phases required (list[str] with min_length=1)
  - Added workout_plan_description, meal_plan_description
  - Changed workout_metadata, meal_metadata from dict to Pydantic models
  - Added _parse_and_validate_dates() helper
  - Refactored build_fitness_plan() to call phase agents per phase
  - Fixed Runner API usage (Runner.run() static method)

### Backend - AI Agent Layer
- **backend/src/ai/app_agents/conversation_agent.py**
  - Updated prompts for temporal information collection
  - Added multi-phase planning guidance
  - Added metadata object creation instructions

- **backend/src/ai/app_agents/workout_phase_agent.py** (NEW)
  - Generates PhaseWorkoutDetails
  - Outputs: workout_cycle, intensity_guidance, volume_notes, progression_notes

- **backend/src/ai/app_agents/meal_phase_agent.py** (NEW)
  - Generates PhaseMealDetails
  - Outputs: daily_calorie_target, macro_split, sample_days, phase_nutrition_focus

### Backend - Service Layer
- **backend/src/services/plan_service.py**
  - Updated save_generated_plan() to extract from new structure
  - Changed workout_plan_output → workout_details
  - Changed meal_plan_output → meal_details
  - Added _extract_workouts_from_cycle() helper
  - Stores training_cycle in workout_plan_details
  - Properly creates Phase records with start_date/end_date

- **backend/src/services/schedule_service.py**
  - Updated to extract training_cycle from phases[].workout_details.workout_cycle
  - Added TODO for multi-phase scheduling support

### Frontend - UI Layer
- **frontend/src/app/dashboard/plan/page.tsx**
  - Updated to display both old and new schema formats (backward compatible)
  - Shows workout_metadata and meal_metadata at plan level
  - Displays phase-specific workout_details and meal_details
  - Collapsible phase details with training cycle and meal plans
  - Maintained legacy display for old schema compatibility

## OpenAI Agents SDK Compliance

### Fixed Issues
1. **No dict fields**: All dict fields converted to Pydantic models with `extra="forbid"`
2. **Runner API**: Changed from `Runner()` constructor to `Runner.run()` static method
3. **Strict schemas**: All models properly validated for strict JSON schema compliance

### Validation
- All Pydantic models use `model_config = {"extra": "forbid"}`
- No `additionalProperties` issues with OpenAI function tools
- Proper type annotations throughout

## Database Schema
No database migrations required. All changes are in the JSON structure stored in:
- `fitness_plans.plan_snapshot` (JSONB column)
- `workout_plans.workout_plan_details` (JSONB column)
- `meal_plans.macronutrient_distribution` (JSONB column)

Existing Phase, WorkoutPlan, MealPlan tables already support the new structure.

## Testing Checklist

### Backend Tests
- [ ] Test plan generation with new schema
- [ ] Verify Phase records created with correct dates
- [ ] Check WorkoutPlan stores training_cycle correctly
- [ ] Verify MealPlan stores phase-specific details
- [ ] Test schedule generation with new workout_cycle location
- [ ] Verify database persistence and retrieval

### Frontend Tests
- [ ] Display plan-level workout_metadata correctly
- [ ] Display plan-level meal_metadata correctly
- [ ] Show phase-specific workout_details
- [ ] Show phase-specific meal_details
- [ ] Verify training cycle display per phase
- [ ] Verify sample meal plans display per phase
- [ ] Test backward compatibility with old schema

### Integration Tests
- [ ] End-to-end plan creation flow
- [ ] Schedule creation from plan
- [ ] Plan display in frontend
- [ ] Phase progression logic
- [ ] Date validation and calculation

## Migration Strategy

### For Existing Data
No migration required - old plans will continue to work through backward compatibility in frontend.

### For New Plans
All new plans will use the new schema structure automatically.

### Graceful Degradation
Frontend displays both old and new schema formats, checking for:
1. New fields first (workout_metadata, meal_metadata, phases[].workout_details)
2. Fallback to old fields (workout_plan, meal_plan)
3. Default values when neither exists

## Next Steps

1. **Complete Testing**
   - Write unit tests for new schema models
   - Create integration tests for full flow
   - Test edge cases (single phase, multiple phases, date boundaries)

2. **Multi-Phase Scheduling**
   - Update schedule_service.py to handle phase transitions
   - Implement phase-specific schedule entries
   - Add logic to switch between phase workout cycles

3. **Frontend Enhancements**
   - Add phase progress indicators
   - Show current phase highlighting
   - Display phase transition dates
   - Add phase-specific metrics

4. **Documentation Updates**
   - Update API documentation with new schema
   - Document phase agent behavior
   - Add examples of multi-phase plans
   - Update user-facing documentation

## Benefits Achieved

1. **Temporal Awareness**: Plans know exactly when they start and end
2. **Progressive Planning**: AI creates proper phase progression automatically
3. **Reduced Redundancy**: Metadata defined once, not per phase
4. **Clear Separation**: Strategy (metadata) vs. implementation (phase details)
5. **Specialized Agents**: Each agent has focused responsibility
6. **Scalability**: Easy to add more phases or phase types
7. **Type Safety**: Full Pydantic validation throughout
8. **SDK Compliance**: No OpenAI Agents SDK compatibility issues
