# Flexible Meal Scheduling Implementation

## Overview

Implemented flexible AI-driven scheduling for grocery shopping and meal prep that supports **any frequency pattern**, not just weekly intervals. This enables the AI to create schedules like:
- Shopping every 15 days
- Meal prep every 10 days
- Twice monthly shopping (1st and 15th)
- Irregular patterns based on user's lifestyle

## Key Changes

### 1. AI Schema Updates (`backend/src/ai/schemas.py`)

Added two new schedule entry models:

#### GroceryShoppingScheduleEntry
```python
class GroceryShoppingScheduleEntry(BaseModel):
    day_offset: int = Field(ge=0, description="Days from plan start (0=start)")
    time: str = Field(description="Shopping time, e.g. '10:00 AM' or '14:30'")
    duration_minutes: int = Field(ge=15, le=180, default=60)
    notes: str | None = Field(None, description="Optional notes")
    repeats_every: int | None = Field(None, description="Days between repeats (7=weekly, 15=every 15 days, None=one-time)")
```

#### MealPrepScheduleEntry
```python
class MealPrepScheduleEntry(BaseModel):
    day_offset: int = Field(ge=0, description="Days from plan start")
    time: str = Field(description="Prep session time")
    session_index: int = Field(ge=0, description="Index into meal_prep_sessions list")
    repeats_every: int | None = Field(None, description="Days between repeats")
    notes: str | None = None
```

#### Updated PhaseMealDetails
Replaced vague frequency strings with explicit schedule lists:
- ❌ `grocery_shopping_frequency: str` (was: "once_per_week", "twice_per_week")
- ✅ `grocery_shopping_schedule: list[GroceryShoppingScheduleEntry]`
- ❌ `meal_prep_preference: str` (was: "batch_prep", "fresh_daily", "mixed")
- ✅ `meal_prep_schedule: list[MealPrepScheduleEntry]`

### 2. Schedule Service Refactoring (`backend/src/services/schedule_service.py`)

#### _generate_grocery_shopping_entries()
**Before:** Rigid weekly logic with hardcoded day calculations
```python
days_between_shops = {
    "once_per_week": 7,
    "twice_per_week": 3,
    "as_needed": 7,
}.get(shopping_frequency, 7)
```

**After:** Flexible AI-driven scheduling
```python
for schedule_entry in shopping_schedule:
    day_offset = schedule_entry.get("day_offset", 0)
    repeats_every = schedule_entry.get("repeats_every")  # Can be None
    first_date = start_date + timedelta(days=day_offset)
    # Create one-time or repeating entries based on repeats_every
```

#### _generate_meal_prep_entries()
**Before:** Hardcoded Sunday/Wednesday prep days
```python
if meal_prep_preference == "batch_prep":
    prep_day_offset = 6  # Sunday
else:
    prep_days = [6, 2]  # Sunday and Wednesday
```

**After:** Flexible AI-driven scheduling with session indexing
```python
for schedule_entry in prep_schedule:
    day_offset = schedule_entry.get("day_offset", 0)
    session_index = schedule_entry.get("session_index", 0)
    repeats_every = schedule_entry.get("repeats_every")
    session = prep_sessions[session_index]
    # Create entries with any frequency pattern
```

#### New Helper Method: _parse_time_string()
Parses various time formats:
- 12-hour: `'10:00 AM'`, `'2:30 PM'`
- 24-hour: `'14:30'`, `'08:00'`
- Default fallback: `10:00` if parsing fails

### 3. AI Agent Instructions (`backend/src/ai/app_agents/meal_phase_agent.py`)

Updated meal phase agent with extensive scheduling examples:

#### Grocery Shopping Schedule Examples
```python
# Weekly on Sundays
[{"day_offset": 6, "time": "10:00 AM", "repeats_every": 7}]

# Every 15 days
[{"day_offset": 0, "time": "10:00 AM", "repeats_every": 15}]

# Twice weekly (Sun/Wed)
[
  {"day_offset": 0, "time": "10:00 AM", "repeats_every": 7},
  {"day_offset": 3, "time": "6:00 PM", "repeats_every": 7}
]

# Twice monthly (1st and 15th)
[
  {"day_offset": 0, "time": "10:00 AM", "repeats_every": 30},
  {"day_offset": 14, "time": "10:00 AM", "repeats_every": 30}
]
```

#### Meal Prep Schedule Examples
```python
# Weekly Sunday prep
[{"day_offset": 6, "time": "2:00 PM", "session_index": 0, "repeats_every": 7}]

# Twice weekly (different sessions)
[
  {"day_offset": 0, "time": "2:00 PM", "session_index": 0, "repeats_every": 7, "notes": "Big batch prep"},
  {"day_offset": 3, "time": "6:00 PM", "session_index": 1, "repeats_every": 7, "notes": "Quick refresh"}
]

# Every 10 days
[{"day_offset": 0, "time": "1:00 PM", "session_index": 0, "repeats_every": 10}]
```

## Scheduling Patterns Supported

### Frequency Examples
| Pattern | `repeats_every` value | Use Case |
|---------|----------------------|----------|
| Weekly | `7` | Standard weekly routine |
| Biweekly | `14` | Every other week |
| Every 10 days | `10` | Custom schedule |
| Every 15 days | `15` | Requested user case |
| Monthly | `30` | Once per month |
| One-time | `None` | Special events |

### Day Offset Examples
| `day_offset` | Meaning | Example |
|--------------|---------|---------|
| `0` | Plan start date | First day of plan |
| `6` | First Sunday | If plan starts Monday, day 6 is Sunday |
| `14` | Two weeks in | Mid-month event |

## Architecture Philosophy

### Before: Service-Heavy Logic
- Schedule service **interpreted** vague preferences
- Hardcoded business logic (e.g., "twice_per_week = every 3 days")
- Limited to weekly-based patterns
- Changes required code modifications

### After: AI-Driven Explicit Scheduling
- AI agent **generates explicit schedules**
- Schedule service is **dumb executor**
- Supports **any frequency pattern**
- Changes only require prompt updates

### Analogy: Workout Scheduling
This follows the same pattern as existing workout scheduling:
- Workouts use `training_cycle` with day offsets
- Meals now use same approach with `day_offset` + `repeats_every`
- Consistent architecture across schedule types

## Database Schema

No database changes required! Existing columns support the new approach:
- `grocery_list` (JSONB) - Stores shopping list data
- `prep_instructions` (JSONB) - Stores meal prep session data
- Both columns already existed from previous migration (83adbc68b3fa)

## Testing Notes

### Test Cases to Validate
1. **Weekly patterns**: Shopping every 7 days, prep every 7 days
2. **Custom frequencies**: Every 10 days, every 15 days
3. **Multiple events**: Shopping Sun+Wed, Prep Sun+Thu
4. **One-time events**: `repeats_every=None` should create single entry
5. **Time parsing**: Test '10:00 AM', '14:30', '2:00 PM' formats
6. **Edge cases**: Empty schedules, invalid session_index, dates beyond plan

### Manual Testing Steps
1. Create a meal plan with custom shopping (e.g., "I shop every 15 days")
2. Check intake specialist extracts this preference
3. Verify meal phase agent generates appropriate schedule
4. Confirm schedule service creates correct entries
5. Validate dates align with repeats_every pattern

## Example AI Output

```json
{
  "grocery_shopping_schedule": [
    {
      "day_offset": 0,
      "time": "10:00 AM",
      "duration_minutes": 90,
      "notes": "First big shop - bring cooler bags",
      "repeats_every": 15
    }
  ],
  "meal_prep_sessions": [
    {
      "session_name": "Biweekly Mega Prep",
      "duration_minutes": 180,
      "recipes": ["Grilled Chicken", "Rice", "Vegetables"],
      "batch_size": 15,
      "instructions": ["Step 1...", "Step 2..."],
      "storage_instructions": "Freeze half, refrigerate rest"
    }
  ],
  "meal_prep_schedule": [
    {
      "day_offset": 1,
      "time": "2:00 PM",
      "session_index": 0,
      "repeats_every": 15,
      "notes": "Day after shopping - fresh ingredients"
    }
  ]
}
```

This creates:
- Shopping on day 0, 15, 30, 45, etc. at 10:00 AM
- Meal prep on day 1, 16, 31, 46, etc. at 2:00 PM

## Benefits

1. **Flexibility**: Supports any frequency pattern user requests
2. **AI-Driven**: Agent decides best schedule based on context
3. **Maintainability**: Logic in prompts, not code
4. **Consistency**: Same pattern as workout scheduling
5. **User-Centric**: Adapts to real-world schedules (e.g., "every 15 days")

## Related Files

- `backend/src/ai/schemas.py` - Pydantic models for AI output
- `backend/src/services/schedule_service.py` - Schedule generation logic
- `backend/src/ai/app_agents/meal_phase_agent.py` - AI agent instructions
- `backend/src/models/schedule.py` - Database model (unchanged)
- `backend/alembic/versions/20251213_0824_83adbc68b3fa_*.py` - Previous migration

## Future Enhancements

1. **Frontend Components**: Display shopping/prep schedules (Tasks 8-9)
2. **Calendar Integration**: Export to iCal, Google Calendar
3. **Notifications**: Remind users before shopping/prep sessions
4. **Adaptive Scheduling**: AI adjusts schedule based on completion history
5. **Multi-Phase Support**: Different schedules per phase (currently uses Phase 1)
