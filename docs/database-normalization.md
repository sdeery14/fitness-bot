# Database Normalization - Grocery Trips and Meal Prep Sessions

## Overview

Completed full normalization of grocery shopping and meal prep data, moving from JSONB `plan_snapshot` storage to proper PostgreSQL tables with foreign key relationships.

## Motivation

- **MCP Server Integration**: PostgreSQL MCP server can now directly query grocery trips and meal prep sessions
- **Data Integrity**: Foreign key constraints enforce referential integrity
- **Query Performance**: Indexed phase_id enables efficient filtering and joins
- **Flexibility**: Individual records can be updated without modifying entire plan_snapshot
- **Type Safety**: Database schema validates data structure

## Changes Made

### Database Schema

#### Migration: `20251215_1400_add_phase_grocery_meal_prep_links.py`

Added to `grocery_shopping_trips` table:
- `phase_id` (UUID, FK to phases.id)
- `target_day_name` (VARCHAR(20)) - e.g., 'Sunday', 'Wednesday'
- `time` (TIME) - Time of day for shopping
- `repeats_every` (INTEGER) - Days between occurrences

Added to `meal_prep_sessions` table:
- `phase_id` (UUID, FK to phases.id)
- `target_day_name` (VARCHAR(20)) - e.g., 'Sunday', 'Wednesday'
- `time` (TIME) - Time of day for prep
- `repeats_every` (INTEGER) - Days between occurrences

Made `plan_snapshot` nullable (step toward eventual removal).

### Model Updates

#### `GroceryShoppingTrip` ([grocery_trip.py](d:\projects\fitness-bot\backend\src\models\grocery_trip.py))

```python
phase_id: Mapped[UUID | None] = mapped_column(
    PGUUID(as_uuid=True),
    ForeignKey("phases.id", ondelete="CASCADE"),
    nullable=True,
    index=True
)
target_day_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
time: Mapped[datetime | None] = mapped_column(Time, nullable=True)
repeats_every: Mapped[int | None] = mapped_column(Integer, nullable=True)

# Relationships
phase: Mapped["Phase | None"] = relationship("Phase", back_populates="grocery_trips")
```

#### `MealPrepSession` ([meal_prep.py](d:\projects\fitness-bot\backend\src\models\meal_prep.py))

```python
phase_id: Mapped[UUID | None] = mapped_column(
    PGUUID(as_uuid=True),
    ForeignKey("phases.id", ondelete="CASCADE"),
    nullable=True,
    index=True
)
target_day_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
time: Mapped[datetime | None] = mapped_column(Time, nullable=True)
repeats_every: Mapped[int | None] = mapped_column(Integer, nullable=True)

# Relationships
phase: Mapped["Phase | None"] = relationship("Phase", back_populates="meal_prep_sessions")
```

#### `Phase` ([fitness_plan.py](d:\projects\fitness-bot\backend\src\models\fitness_plan.py#L85-L86))

```python
grocery_trips = relationship("GroceryShoppingTrip", back_populates="phase", cascade="all, delete-orphan")
meal_prep_sessions = relationship("MealPrepSession", back_populates="phase", cascade="all, delete-orphan")
```

### Service Layer Changes

#### PlanService ([plan_service.py](d:\projects\fitness-bot\backend\src\services\plan_service.py#L644-L718))

Added logic in `save_generated_plan()` to create normalized records:

**Grocery Trips** (lines 644-682):
- Extracts `grocery_shopping_schedule` from AI-generated meal_details
- Parses time strings (supports "09:00" and "9:00 AM" formats)
- Creates `GroceryShoppingTrip` records linked to phases
- Stores schedule metadata: `target_day_name`, `time`, `repeats_every`

**Meal Prep Sessions** (lines 684-718):
- Extracts `meal_prep_schedule` from AI-generated meal_details
- Parses time strings (supports "18:00" and "6:00 PM" formats)
- Creates `MealPrepSession` records linked to phases
- Stores schedule metadata: `target_day_name`, `time`, `repeats_every`

#### ScheduleService ([schedule_service.py](d:\projects\fitness-bot\backend\src\services\schedule_service.py))

Completely rewrote schedule generation functions:

**`_generate_grocery_shopping_entries()` (lines 597-677)**:
- **Before**: Read from `plan_snapshot.phases[0].meal_details.grocery_shopping_schedule`
- **After**: Query `GroceryShoppingTrip` table joined with `Phase`
- Uses phase boundaries for scheduling (entries only within phase dates)
- Calculates `day_offset` programmatically from `target_day_name`

**`_generate_meal_prep_entries()` (lines 701-781)**:
- **Before**: Read from `plan_snapshot.phases[0].meal_details.meal_prep_schedule`
- **After**: Query `MealPrepSession` table joined with `Phase`
- Uses phase boundaries for scheduling (entries only within phase dates)
- Calculates `day_offset` programmatically from `target_day_name`

## Data Flow

### Plan Generation → Database

```
AI Agent (meal_phase_agent.py)
  ↓ generates
FitnessPlanOutput (schemas.py)
  ↓ contains grocery_shopping_schedule & meal_prep_schedule
plan_service.save_generated_plan()
  ↓ extracts and saves
GroceryShoppingTrip & MealPrepSession records
  ↓ linked to
Phase records
```

### Schedule Creation

```
schedule_service.create_schedule()
  ↓ calls
_generate_grocery_shopping_entries()
  ↓ queries
grocery_shopping_trips WHERE phase_id IN (phases of plan)
  ↓ creates
ScheduleEntry records with grocery_trip_id

_generate_meal_prep_entries()
  ↓ queries  
meal_prep_sessions WHERE phase_id IN (phases of plan)
  ↓ creates
ScheduleEntry records with meal_prep_session_id
```

## MCP Server Queries

Now possible with PostgreSQL MCP server:

```sql
-- All grocery trips for next week
SELECT gt.name, gt.target_day_name, gt.time, p.name as phase_name
FROM grocery_shopping_trips gt
JOIN phases p ON gt.phase_id = p.id
JOIN fitness_plans fp ON p.fitness_plan_id = fp.id
WHERE fp.user_id = '...'
AND gt.target_day_name IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday');

-- All meal prep sessions in a phase
SELECT mps.session_name, mps.target_day_name, mps.duration_minutes, mps.recipes
FROM meal_prep_sessions mps
WHERE mps.phase_id = '...';

-- Shopping list for specific trip
SELECT gt.name, gt.items, gt.estimated_duration_minutes
FROM grocery_shopping_trips gt
WHERE gt.id = '...';
```

## Benefits Achieved

✅ **Queryable Data**: MCP server can search/analyze grocery and meal prep data  
✅ **Phase-Scoped**: Trips/sessions linked to specific phases (important for multi-phase plans)  
✅ **Flexible Scheduling**: Supports one-time and recurring events with any frequency  
✅ **Type Safety**: Database validates structure (nullable target_day_name requires repeats_every)  
✅ **Referential Integrity**: Cascade deletes when phases/plans removed  
✅ **Performance**: Indexed phase_id for efficient filtering  

## Migration Path

Current state: **Phase 2 - Dual Storage**
- ✅ Phase 1: Create normalized tables
- ✅ Phase 2: Populate both plan_snapshot (for compatibility) and normalized tables
- ⏳ Phase 3: Update all read operations to use normalized tables (done for schedules)
- ⏳ Phase 4: Make plan_snapshot fully optional
- ⏳ Phase 5: Remove plan_snapshot column entirely

## Testing Strategy

1. **Unit Tests**: Verify save_generated_plan creates records with correct phase links
2. **Integration Tests**: Create plan → verify grocery trips and meal prep sessions exist
3. **Schedule Tests**: Verify ScheduleEntry records created with correct dates
4. **Migration Tests**: Apply migration → verify schema changes → rollback → verify clean state
5. **MCP Server Tests**: Verify queries return expected data

## Future Work

- [ ] Add API endpoints for querying grocery trips and meal prep sessions directly
- [ ] Frontend components to display normalized data
- [ ] Phase-specific editing (update grocery trip without affecting whole plan)
- [ ] Analytics: most common shopping days, average prep durations, etc.
- [ ] Remove plan_snapshot column (requires updating all code that reads it)

## Related Documentation

- [Plan Generation Flow](plan-generation-flow.md) - Full plan generation process
- [Flexible Meal Scheduling](flexible-meal-scheduling.md) - Scheduling algorithm details
- [Schema Update Complete](SCHEMA_UPDATE_COMPLETE.md) - Previous normalization work
