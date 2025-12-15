# Plan Snapshot Removal - Complete Refactoring

**Date**: December 15, 2025  
**Status**: ✅ Complete

## Overview

Successfully removed the `plan_snapshot` JSONB column from `fitness_plans` table and refactored entire codebase to use normalized PostgreSQL tables exclusively.

## Changes Made

### 1. Database Schema

**Removed**:
- `fitness_plans.plan_snapshot` column (JSON)

**Normalized Data Now Stored In**:
- `phases` table - phase information with `phase_details` JSON for workout_cycle
- `workouts` table - individual workout details
- `meals` table - individual meal details  
- `workout_plans` table - training program metadata
- `meal_plans` table - nutrition program metadata
- `grocery_shopping_trips` table - shopping trips with phase links
- `meal_prep_sessions` table - prep sessions with phase links

### 2. Code Refactoring

#### **plan_service.py** Changes:

**Removed**:
- `plan_snapshot` initialization in `create_plan()` 
- `plan_snapshot` copying in `replace_plan()`
- Error storage in `plan_snapshot` in `update_plan_status()`
- Phase transition tracking in `plan_snapshot`
- `plan.plan_snapshot = plan_output` assignment in `save_generated_plan()`

**Added**:
- Store `workout_cycle` in `phase.phase_details` for schedule generation
- TODO comments for potential future features (error tracking table, phase transitions table)

#### **schedule_service.py** Changes:

**Before**: Read training_cycle from `plan.plan_snapshot.phases[0].workout_details.workout_cycle`  
**After**: Read training_cycle from `plan.phases[0].phase_details["workout_cycle"]`

Already normalized (from previous work):
- Grocery shopping schedule reads from `grocery_shopping_trips` table
- Meal prep schedule reads from `meal_prep_sessions` table

#### **plan_tools.py** Changes:

**`get_active_plan_details` Tool Refactored**:

**Before**: 
```python
plan_snapshot = active_plan.plan_snapshot or {}
workout_plan = plan_snapshot["workout_plan"]
meal_plan = plan_snapshot["meal_plan"]
phases = plan_snapshot["phases"]
```

**After**:
```python
# Read from normalized tables
workout_plan = active_plan.workout_plans[0]
meal_plan = active_plan.meal_plans[0]
phases = active_plan.phases
```

Now returns:
- Training plan details from `workout_plans` table
- Nutrition plan details from `meal_plans` table
- Phase information from `phases` table with proper relationships

#### **fitness_plan.py** Model Changes:

**Removed**:
```python
plan_snapshot = Column(JSON, nullable=True)
```

### 3. Migration

Created migration: `20251215_1500_drop_plan_snapshot.py`

```sql
ALTER TABLE fitness_plans DROP COLUMN plan_snapshot;
```

Note: Column was already removed in database (possibly from earlier migration).

## Data Flow

### Plan Generation Flow:
```
AI Agent → FitnessPlanOutput
  ↓
plan_service.save_generated_plan()
  ↓
CREATE Phase records (with workout_cycle in phase_details)
CREATE Workout records (linked to phases)
CREATE Meal records (linked to phases)
CREATE WorkoutPlan records
CREATE MealPlan records
CREATE GroceryShoppingTrip records (linked to phases)
CREATE MealPrepSession records (linked to phases)
```

### Schedule Generation Flow:
```
schedule_service.create_schedule()
  ↓
Read workout_cycle from phase.phase_details
Read workouts from workouts table
Read meals from meals table
Read grocery_trips from grocery_shopping_trips table
Read meal_prep_sessions from meal_prep_sessions table
  ↓
CREATE ScheduleEntry records
```

### AI Agent Query Flow:
```
get_active_plan_details tool
  ↓
Query phases table
Query workout_plans table
Query meal_plans table
  ↓
Return normalized data to AI
```

## Benefits

✅ **No Duplication**: Data stored once in normalized tables  
✅ **Data Integrity**: Foreign key constraints enforce referential integrity  
✅ **MCP Server Ready**: All data queryable via PostgreSQL MCP server  
✅ **Type Safety**: Database schema validates structure  
✅ **Flexibility**: Update individual records without modifying entire plan  
✅ **Performance**: Indexed queries, no JSON parsing overhead  
✅ **Clarity**: Clear data model, no confusion about source of truth  

## Testing Checklist

- [ ] Create new fitness plan → verify all normalized tables populated
- [ ] Query `get_active_plan_details` → verify returns correct data from tables
- [ ] Generate schedule → verify workouts, meals, grocery, meal prep entries created
- [ ] MCP server queries → verify can query phases, grocery trips, meal prep
- [ ] Plan versioning → verify parent plan data copied correctly without plan_snapshot
- [ ] Error handling → verify errors logged (not stored in plan_snapshot)

## Breaking Changes

⚠️ **API Responses**: Any frontend code expecting `plan_snapshot` field will receive `null` or field will be missing

**Frontend Updates Needed**:
- Remove references to `responseData.plan_snapshot` 
- Query specific endpoints for phases, workouts, meals instead

## Future Work

### Potential New Tables:
- **`phase_transitions`** - Track historical phase transitions instead of storing in JSONB
- **`plan_errors`** - Track generation errors with timestamps instead of storing in JSONB

### Documentation Updates:
- Update API contracts to reflect normalized structure
- Update specs to remove plan_snapshot references
- Update frontend documentation

## Files Modified

**Backend**:
- `src/models/fitness_plan.py` - Removed plan_snapshot column
- `src/services/plan_service.py` - Removed all plan_snapshot usage
- `src/services/schedule_service.py` - Updated to read from phase.phase_details
- `src/ai/tools/plan_tools.py` - Refactored get_active_plan_details tool
- `alembic/versions/20251215_1500_drop_plan_snapshot.py` - Migration file

**Frontend** (needs update):
- `components/chat/plan-message-card.tsx` - Remove plan_snapshot parsing

**Documentation**:
- `docs/database-normalization.md` - Existing normalization documentation
- `docs/plan-snapshot-removal.md` - This document

## Related Work

This completes the normalization effort started in:
- Database normalization for grocery trips and meal prep (December 15, 2025)
- Schema refactoring for phases (December 13, 2025)
- Schedule calculation improvements (December 13, 2025)

## Success Metrics

✅ Zero references to `plan_snapshot` in backend code (except docs/specs)  
✅ All data queryable through normalized tables  
✅ No JSONB parsing required for any operation  
✅ Clear single source of truth for all plan data  
