# External Integrations - Implementation Summary

## Overview
Phase 3 External Integrations provides curated data sources for AI-powered fitness plan generation.

## Completed Integrations

### 1. USDA FoodData Central API Client
**File:** `backend/src/integrations/usda_fooddata.py`

**Purpose:** Retrieve accurate nutritional data for meal planning

**Key Features:**
- Search USDA food database (Foundation, SR Legacy, Survey, Branded)
- Get detailed nutrient profiles by FDC ID
- Calculate portion-scaled nutritional values (g, oz, lb)
- Support for macro/micronutrient tracking

**Methods:**
```python
async def search_foods(query, data_type, page_size, page_number, brand_owner) -> dict
async def get_food_details(fdc_id) -> dict
async def calculate_portions(fdc_id, quantity, unit) -> dict
async def search_and_calculate(query, quantity, unit) -> dict
```

**Usage Example:**
```python
from src.integrations.usda_fooddata import usda_client

# Search for foods
results = await usda_client.search_foods("chicken breast", data_type=["Foundation"])

# Calculate nutrition for 6oz portion
nutrition = await usda_client.calculate_portions(
    fdc_id="171477",  # Chicken breast
    quantity=6,
    unit="oz"
)
# Returns: calories, protein_grams, carbs_grams, fats_grams, fiber_grams
```

**Functional Requirements Satisfied:**
- FR-044: USDA FoodData Central integration
- FR-045: Accurate ingredient nutritional data
- FR-046: Dietary restriction filtering (via ingredient data)

### 2. Curated Exercise Database
**File:** `backend/src/integrations/exercise_database.py`

**Purpose:** Comprehensive exercise library for workout generation

**Key Features:**
- 28 curated exercises covering all major muscle groups
- Equipment filtering (bodyweight, dumbbells, barbell, machines, etc.)
- Difficulty levels (beginner, intermediate, advanced)
- Alternative exercise recommendations
- Detailed form cues and instructions

**Exercise Categories:**
- **Chest:** 5 exercises (bench press variations, push-ups, cable fly)
- **Back:** 5 exercises (deadlifts, pull-ups, rows, lat pulldown)
- **Shoulders:** 3 exercises (overhead press, lateral raise, face pull)
- **Legs:** 5 exercises (squats, RDL, leg press, Bulgarian split squat, leg curl)
- **Arms:** 4 exercises (barbell curl, tricep dip, hammer curl, tricep pushdown)
- **Core:** 3 exercises (plank, Russian twist, hanging leg raise)
- **Cardio:** 3 exercises (treadmill running, burpee, jump rope)

**Query Functions:**
```python
from src.integrations.exercise_database import (
    get_exercises_by_muscle_group,
    get_exercises_by_equipment,
    get_exercises_by_difficulty,
    get_exercise_by_name,
    get_alternative_exercises,
    EXERCISE_DATABASE
)

# Get chest exercises
chest_exercises = get_exercises_by_muscle_group("chest")

# Filter by available equipment
home_exercises = get_exercises_by_equipment(["dumbbells", "bodyweight"])

# Get alternatives for an exercise
alternatives = get_alternative_exercises("barbell_bench_press")
# Returns: dumbbell_bench_press, push_up, machine_chest_press
```

**Equipment Support:**
- Bodyweight (4 exercises)
- Dumbbells (5 exercises)
- Barbell (8 exercises)
- Bench (4 exercises)
- Cable machine (4 exercises)
- Pull-up bar (2 exercises)
- And more...

**Difficulty Distribution:**
- Beginner: 15 exercises (54%)
- Intermediate: 12 exercises (43%)
- Advanced: 1 exercise (3%)

**Functional Requirements Satisfied:**
- FR-048: Curated exercise database
- FR-049: Target muscle groups
- FR-050: Equipment filtering
- FR-051: Alternative exercises

## Architecture

### USDA Integration Pattern
```
AI Meal Plan Agent
  ↓
usda_client.search_and_calculate()
  ↓
USDA FoodData Central API (https://api.nal.usda.gov/fdc/v1)
  ↓
Scaled nutritional values
  ↓
Meal.meal_details JSON (includes usda_fdc_id)
  ↓
PostgreSQL meals table
```

### Exercise Database Pattern
```
AI Workout Plan Agent
  ↓
get_exercises_by_muscle_group() + get_exercises_by_equipment()
  ↓
EXERCISE_DATABASE (in-memory reference data)
  ↓
Exercise model instances created
  ↓
PostgreSQL exercises table (linked to workouts)
```

## Key Design Decisions

### 1. USDA API Client as Singleton
**Rationale:** Avoid repeated API key validation and client instantiation

**Implementation:**
```python
usda_client = USDAFoodDataClient() if settings.USDA_API_KEY else None
```

### 2. Exercise Database as Reference Data
**Rationale:** Exercise model requires workout_id foreign key, so can't pre-insert standalone records

**Implementation:** 
- Store curated exercises as Python constants (EXERCISE_DATABASE list)
- AI agents query this data when generating plans
- Create Exercise model instances only when linked to specific workouts

### 3. Portion Calculation with Unit Conversion
**Rationale:** Users think in oz/lb, USDA stores per 100g

**Implementation:**
```python
scale_factor = quantity / 100  # Base
if unit == "oz": scale_factor = (quantity * 28.35) / 100
elif unit == "lb": scale_factor = (quantity * 453.592) / 100
```

## Testing Considerations

### USDA Client Tests
- Mock httpx responses for API calls
- Test portion calculations with known values
- Test error handling (invalid FDC ID, missing API key)
- Test data_type filtering

### Exercise Database Tests
- Test query functions return correct results
- Test equipment filtering logic
- Test alternative exercise lookups
- Test difficulty filtering

## Next Steps

With external integrations complete, proceed to:

1. **Phase 3: AI Agents (T044-T052)** - Multi-agent orchestration
   - Base agent initialization
   - Conversation Agent (requirement extraction)
   - Fitness Plan Agent (plan coordination)
   - Workout Plan Agent (uses exercise database)
   - Meal Plan Agent (uses USDA client)
   - AI tools for plan creation

2. **Phase 3: Services (T053-T058)** - Business logic layer
   - AuthService (JWT, bcrypt)
   - UserService (CRUD)
   - PlanService (PostgreSQL persistence)
   - AI orchestration (multi-agent workflow)
   - Background workers (Celery tasks)

3. **Phase 3: API Endpoints (T059-T064)** - REST API
4. **Phase 3: Frontend (T065-T076)** - Next.js UI
5. **Phase 3: Testing (T077-T084)** - 80% coverage

## Configuration Required

### USDA API Key
Get free API key at: https://fdc.nal.usda.gov/api-key-signup.html

Add to `backend/.env`:
```env
USDA_API_KEY=your_api_key_here
```

## Status
✅ **Phase 3 External Integrations: COMPLETE**
- T041: USDA FoodData Central API client
- T042: Curated exercise database seed script
- T043: Exercise database ready for AI consumption

**Overall Progress:** 43/164 tasks (26%), 43/84 MVP tasks (51%)
