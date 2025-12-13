# Data Model: AI-Powered Fitness Planner

**Feature**: 001-ai-fitness-planner  
**Date**: 2025-11-15  
**Database**: PostgreSQL 15+ with JSONB support

## Overview

This document defines the data model for the AI-powered fitness planning application. The schema supports all functional requirements including user management, fitness plan creation, workout/meal planning, daily scheduling, progress tracking, and conversational AI interaction.

The model uses PostgreSQL's relational capabilities for structured data with JSONB columns for AI-generated content snapshots, enabling both strong data integrity and flexibility.

---

## Entity Relationship Diagram

```
User
  |
  +--< FitnessPlan (1:N)
  |      |
  |      +--< Phase (1:N)
  |      |
  |      +--< WorkoutPlan (1:1)
  |      |      |
  |      |      +--< Workout (1:N)
  |      |             |
  |      |             +--< Exercise (1:N)
  |      |
  |      +--< MealPlan (1:1)
  |             |
  |             +--< Meal (1:N)
  |
  +--< Schedule (1:1)
  |      |
  |      +--< ScheduleEntry (1:N)
  |
  +--< ProgressRecord (1:N)
  |
  +--< Conversation (1:N)
        |
        +--< Message (1:N)
        |
        +--< DisruptionEvent (1:N)
```

---

## Core Entities

### 1. User

Represents an individual using the application.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Profile information
    current_fitness_level VARCHAR(50),  -- beginner, intermediate, advanced
    date_of_birth DATE,
    gender VARCHAR(20),  -- optional, for fitness calculations
    
    -- Preferences
    dietary_restrictions TEXT[],  -- ['vegan', 'gluten-free', ...]
    equipment_access TEXT[],      -- ['home', 'gym', 'minimal']
    preferred_workout_days TEXT[], -- ['monday', 'wednesday', 'friday']
    
    -- Settings
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_preferences JSONB DEFAULT '{"workout_reminders": true, "meal_reminders": false}',
    
    -- Soft delete
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

**Attributes**:
- `id`: Unique identifier (UUID for distributed systems)
- `email`: Login credential, unique
- `password_hash`: Secure password storage (never plaintext)
- `current_fitness_level`: Informs plan difficulty
- `dietary_restrictions`: Influences meal planning
- `equipment_access`: Determines available exercises
- `notification_preferences`: User communication settings

**Validation Rules**:
- Email must be valid format
- Password must be hashed with bcrypt (never store plaintext)
- Timezone must be valid IANA timezone string
- Dietary restrictions from predefined list

**Relationships**:
- Has many `FitnessPlans` (one active at a time)
- Has one active `Schedule`
- Has many `ProgressRecords`
- Has many `Conversations`

---

### 2. FitnessPlan

Represents a complete plan to achieve a fitness goal.

```sql
CREATE TABLE fitness_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Plan metadata
    goal_description TEXT NOT NULL,
    goal_type VARCHAR(50) NOT NULL,  -- weight_loss, muscle_gain, endurance, general_health, event_prep
    duration_weeks INT NOT NULL CHECK (duration_weeks > 0),
    
    -- Timeline
    start_date DATE NOT NULL,
    target_end_date DATE NOT NULL,
    actual_end_date DATE,  -- NULL if ongoing, set when completed
    
    -- Status
    current_status VARCHAR(50) DEFAULT 'active',  -- active, completed, paused, abandoned
    current_phase_number INT DEFAULT 1,
    
    -- AI-generated content snapshot
    plan_snapshot JSONB NOT NULL,  -- Full plan structure from AI
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generated_by_model VARCHAR(100),  -- e.g., 'gpt-4-turbo-2024-11-15'
    generation_prompt TEXT,  -- Original user prompt
    
    CONSTRAINT valid_dates CHECK (target_end_date > start_date)
);

CREATE INDEX idx_fitness_plans_user_id ON fitness_plans(user_id);
CREATE INDEX idx_fitness_plans_status ON fitness_plans(current_status);
CREATE INDEX idx_fitness_plans_user_status ON fitness_plans(user_id, current_status);
CREATE INDEX idx_fitness_plans_dates ON fitness_plans(start_date, target_end_date);

-- JSONB index for querying plan structure
CREATE INDEX idx_fitness_plans_snapshot ON fitness_plans USING GIN (plan_snapshot);
```

**Attributes**:
- `goal_description`: User's stated goal (e.g., "lose 15 pounds in 3 months")
- `goal_type`: Categorization for analytics and filtering
- `duration_weeks`: Planned duration (can extend due to disruptions)
- `current_phase_number`: For multi-phase plans, tracks current phase
- `plan_snapshot`: JSONB containing full AI-generated plan structure

**plan_snapshot JSONB Structure**:
```json
{
  "version": "1.0",
  "generated_at": "2025-11-15T10:30:00Z",
  "model_version": "gpt-4-turbo-2024-11-15",
  "goal_summary": "Lose 15 pounds in 12 weeks through balanced diet and progressive strength training",
  "overall_strategy": {
    "workout_frequency": "4 days per week",
    "cardio_focus": "30%",
    "strength_focus": "70%",
    "nutrition_approach": "500 calorie deficit, high protein"
  },
  "phases": [
    {
      "phase_number": 1,
      "name": "Foundation Building",
      "duration_weeks": 4,
      "objectives": ["Build exercise habit", "Establish baseline fitness"],
      "workout_changes": "3 sets, moderate weight, focus on form",
      "nutrition_changes": "Track food intake, 1800 calories/day"
    }
  ],
  "progression_notes": "Increase weight by 5-10% every 2 weeks if form is maintained"
}
```

**Validation Rules**:
- `duration_weeks` must be positive
- `target_end_date` must be after `start_date`
- Only one `active` plan per user at a time (enforced at application level)
- `plan_snapshot` must be valid JSON

**Relationships**:
- Belongs to `User`
- Has many `Phases`
- Has one `WorkoutPlan`
- Has one `MealPlan`

---

### 3. Phase

Represents a distinct period within a multi-phase fitness plan.

```sql
CREATE TABLE phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fitness_plan_id UUID NOT NULL REFERENCES fitness_plans(id) ON DELETE CASCADE,
    
    phase_number INT NOT NULL,
    name VARCHAR(255) NOT NULL,  -- e.g., "Foundation Building", "Strength Phase"
    objectives TEXT[] NOT NULL,   -- ["Build habit", "Increase strength"]
    
    duration_weeks INT NOT NULL CHECK (duration_weeks > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    status VARCHAR(50) DEFAULT 'not_started',  -- not_started, in_progress, completed
    
    -- Phase-specific details
    phase_details JSONB,  -- Workout intensity, nutrition adjustments, etc.
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_phase_dates CHECK (end_date > start_date),
    CONSTRAINT unique_phase_number UNIQUE (fitness_plan_id, phase_number)
);

CREATE INDEX idx_phases_fitness_plan ON phases(fitness_plan_id);
CREATE INDEX idx_phases_dates ON phases(start_date, end_date);
CREATE INDEX idx_phases_status ON phases(status);
```

**Attributes**:
- `phase_number`: Sequential numbering (1, 2, 3...)
- `name`: Descriptive phase name
- `objectives`: Array of phase goals
- `phase_details`: JSONB for phase-specific configuration

**Validation Rules**:
- `phase_number` must be unique per `fitness_plan_id`
- Phase dates must not overlap within same plan (enforced at application level)
- `end_date` must be after `start_date`

**Relationships**:
- Belongs to `FitnessPlan`

---

### 4. WorkoutPlan

Component of a fitness plan defining exercise routines.

```sql
CREATE TABLE workout_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fitness_plan_id UUID NOT NULL REFERENCES fitness_plans(id) ON DELETE CASCADE,
    
    workout_frequency_per_week INT NOT NULL CHECK (workout_frequency_per_week BETWEEN 1 AND 7),
    rest_day_strategy VARCHAR(100),  -- e.g., "Active recovery on rest days"
    progression_strategy TEXT,
    
    -- Configuration
    workout_plan_details JSONB,  -- Structure, split type (full body, upper/lower, PPL)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT one_workout_plan_per_fitness_plan UNIQUE (fitness_plan_id)
);

CREATE INDEX idx_workout_plans_fitness_plan ON workout_plans(fitness_plan_id);
```

**Attributes**:
- `workout_frequency_per_week`: Number of workout days
- `rest_day_strategy`: How rest days are handled
- `progression_strategy`: How difficulty increases over time

**Relationships**:
- Belongs to `FitnessPlan` (1:1)
- Has many `Workouts`

---

### 5. Workout

Represents a single workout session.

```sql
CREATE TABLE workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_plan_id UUID NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES phases(id) ON DELETE SET NULL,  -- Optional phase association
    
    name VARCHAR(255) NOT NULL,
    workout_type VARCHAR(100),  -- strength, cardio, flexibility, mixed
    target_muscle_groups TEXT[],
    
    estimated_duration_minutes INT,
    intensity_level VARCHAR(50),  -- low, moderate, high, very_high
    
    -- Workout details
    description TEXT,
    workout_structure JSONB NOT NULL,  -- List of exercises with sets/reps
    
    -- Scheduling (which days of week this workout is typically done)
    typical_day_of_week INT[],  -- [1, 4] for Monday and Thursday (1=Monday, 7=Sunday)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workouts_workout_plan ON workouts(workout_plan_id);
CREATE INDEX idx_workouts_phase ON workouts(phase_id);
CREATE INDEX idx_workouts_type ON workouts(workout_type);
```

**workout_structure JSONB Example**:
```json
{
  "warmup": {
    "duration_minutes": 5,
    "activities": ["Light cardio", "Dynamic stretching"]
  },
  "main_exercises": [
    {
      "order": 1,
      "exercise_id": "uuid-reference",
      "sets": 3,
      "reps": "8-12",
      "rest_seconds": 60,
      "notes": "Focus on controlled movement"
    }
  ],
  "cooldown": {
    "duration_minutes": 5,
    "activities": ["Static stretching"]
  }
}
```

**Relationships**:
- Belongs to `WorkoutPlan`
- Optionally belongs to `Phase`
- Has many `Exercises`

---

### 6. Exercise

Represents an individual exercise within a workout.

```sql
CREATE TABLE exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id UUID NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
    
    exercise_order INT NOT NULL,  -- Order within workout
    
    name VARCHAR(255) NOT NULL,
    exercise_type VARCHAR(100),  -- compound, isolation, cardio, flexibility
    target_muscle_groups TEXT[] NOT NULL,
    equipment_required TEXT[],  -- ['barbell', 'bench'], ['bodyweight'], ['dumbbells']
    
    -- Prescription
    sets INT,
    reps VARCHAR(50),  -- "8-12" or "AMRAP" or "30 seconds"
    weight_guidance VARCHAR(100),  -- "60% of 1RM" or "challenging but doable"
    rest_seconds INT,
    tempo VARCHAR(20),  -- e.g., "2-0-2-0" (eccentric-pause-concentric-pause)
    
    -- Instructions
    instructions TEXT,
    form_cues TEXT[],  -- ["Keep back straight", "Engage core"]
    
    -- Alternatives
    alternative_exercise_ids UUID[],  -- References to other exercises
    modification_notes TEXT,  -- How to make easier/harder
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exercises_workout ON exercises(workout_id);
CREATE INDEX idx_exercises_order ON exercises(workout_id, exercise_order);
CREATE INDEX idx_exercises_muscle_groups ON exercises USING GIN (target_muscle_groups);
```

**Attributes**:
- `exercise_order`: Position in workout sequence
- `reps`: Can be numeric ("10") or range ("8-12") or time-based ("30 seconds")
- `alternative_exercise_ids`: Array of exercise IDs that can substitute this one
- `form_cues`: Coaching points for proper technique

**Validation Rules**:
- `exercise_order` must be unique within workout
- `sets` must be positive if specified
- `rest_seconds` must be non-negative

**Relationships**:
- Belongs to `Workout`

---

### 7. MealPlan

Component of a fitness plan defining nutrition strategy.

```sql
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fitness_plan_id UUID NOT NULL REFERENCES fitness_plans(id) ON DELETE CASCADE,
    
    daily_calorie_target INT NOT NULL CHECK (daily_calorie_target > 0),
    macronutrient_distribution JSONB NOT NULL,  -- {"protein_pct": 30, "carb_pct": 40, "fat_pct": 30}
    meals_per_day INT DEFAULT 3 CHECK (meals_per_day BETWEEN 1 AND 6),
    
    dietary_approach VARCHAR(100),  -- balanced, low_carb, high_protein, vegetarian, etc.
    meal_timing_strategy TEXT,
    
    -- Configuration
    meal_plan_details JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT one_meal_plan_per_fitness_plan UNIQUE (fitness_plan_id),
    CONSTRAINT valid_macros CHECK (
        (meal_plan_details->>'protein_pct')::int + 
        (meal_plan_details->>'carb_pct')::int + 
        (meal_plan_details->>'fat_pct')::int = 100
    )
);

CREATE INDEX idx_meal_plans_fitness_plan ON meal_plans(fitness_plan_id);
```

**Attributes**:
- `daily_calorie_target`: Total daily calories
- `macronutrient_distribution`: Protein/carb/fat percentages
- `meals_per_day`: Number of eating occasions

**Validation Rules**:
- Macronutrient percentages must sum to 100
- `daily_calorie_target` must be positive and reasonable (800-5000 range enforced at app level)

**Relationships**:
- Belongs to `FitnessPlan` (1:1)
- Has many `Meals`

---

### 8. Meal

Represents a single meal instance.

```sql
CREATE TABLE meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meal_plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES phases(id) ON DELETE SET NULL,
    
    name VARCHAR(255) NOT NULL,
    meal_type VARCHAR(50) NOT NULL,  -- breakfast, lunch, dinner, snack
    
    -- Nutritional info
    calories INT,
    protein_grams DECIMAL(5,1),
    carbs_grams DECIMAL(5,1),
    fat_grams DECIMAL(5,1),
    
    -- Meal details
    meal_details JSONB NOT NULL,  -- Recipes, ingredients, portions
    
    -- Preparation
    prep_time_minutes INT,
    cook_time_minutes INT,
    difficulty VARCHAR(50),  -- easy, moderate, complex
    
    -- Alternatives
    variation_notes TEXT,  -- How to modify the meal
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meals_meal_plan ON meals(meal_plan_id);
CREATE INDEX idx_meals_phase ON meals(phase_id);
CREATE INDEX idx_meals_type ON meals(meal_type);
```

**meal_details JSONB Example**:
```json
{
  "recipe": "Grilled chicken with quinoa and vegetables",
  "ingredients": [
    {"item": "Chicken breast", "amount": "6 oz", "calories": 280},
    {"item": "Quinoa", "amount": "1 cup cooked", "calories": 220},
    {"item": "Mixed vegetables", "amount": "2 cups", "calories": 100}
  ],
  "instructions": [
    "Season chicken with herbs and grill for 6-8 minutes per side",
    "Cook quinoa according to package directions",
    "Steam or roast vegetables until tender"
  ],
  "meal_timing": "Post-workout meal - high protein and carbs for recovery"
}
```

**Relationships**:
- Belongs to `MealPlan`
- Optionally belongs to `Phase`

---

### 9. Schedule

Represents the user's day-to-day timeline of workouts and meals.

```sql
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fitness_plan_id UUID NOT NULL REFERENCES fitness_plans(id) ON DELETE CASCADE,
    
    start_date DATE NOT NULL,
    
    -- Schedule metadata
    last_recalculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    recalculation_reason TEXT,  -- e.g., "User missed 2 workouts due to illness"
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT one_schedule_per_plan UNIQUE (fitness_plan_id)
);

CREATE INDEX idx_schedules_user ON schedules(user_id);
CREATE INDEX idx_schedules_fitness_plan ON schedules(fitness_plan_id);
```

**Attributes**:
- `start_date`: When schedule begins
- `last_recalculated_at`: Tracks when schedule was last adjusted
- `recalculation_reason`: Audit trail for schedule changes

**Relationships**:
- Belongs to `User`
- Belongs to `FitnessPlan` (1:1)
- Has many `ScheduleEntries`

---

### 10. ScheduleEntry

Represents a specific workout, meal, grocery shopping trip, or meal prep session scheduled for a particular date/time.

```sql
CREATE TABLE schedule_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    
    entry_type VARCHAR(50) NOT NULL,  -- workout, meal, grocery_shopping, meal_prep
    entry_date DATE NOT NULL,
    entry_time TIME,  -- Optional, for meal timing
    
    -- Reference to actual workout or meal
    workout_id UUID REFERENCES workouts(id) ON DELETE SET NULL,
    meal_id UUID REFERENCES meals(id) ON DELETE SET NULL,
    
    -- Grocery shopping data (for entry_type='grocery_shopping')
    grocery_list JSONB,  -- {"items": [{"ingredient": "Chicken breast", "quantity": "2 lbs", "category": "Meat"}, ...]}
    
    -- Meal prep instructions (for entry_type='meal_prep')
    prep_instructions JSONB,  -- {"recipes": [...], "duration_minutes": 90, "instructions": [...], "storage": "..."}
    
    -- Completion tracking
    completion_status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, completed, skipped, rescheduled
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- User notes
    user_notes TEXT,
    skipped_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_entry_reference CHECK (
        (entry_type = 'workout' AND workout_id IS NOT NULL AND meal_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NULL) OR
        (entry_type = 'meal' AND meal_id IS NOT NULL AND workout_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NULL) OR
        (entry_type = 'grocery_shopping' AND workout_id IS NULL AND meal_id IS NULL AND grocery_list IS NOT NULL AND prep_instructions IS NULL) OR
        (entry_type = 'meal_prep' AND workout_id IS NULL AND meal_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NOT NULL)
    )
);

CREATE INDEX idx_schedule_entries_schedule ON schedule_entries(schedule_id);
CREATE INDEX idx_schedule_entries_date ON schedule_entries(entry_date);
CREATE INDEX idx_schedule_entries_user_date ON schedule_entries(schedule_id, entry_date);
CREATE INDEX idx_schedule_entries_status ON schedule_entries(completion_status);
CREATE INDEX idx_schedule_entries_workout ON schedule_entries(workout_id);
CREATE INDEX idx_schedule_entries_meal ON schedule_entries(meal_id);
```

**Attributes**:
- `entry_type`: Discriminator for workout, meal, grocery_shopping, or meal_prep
- `entry_date`: Scheduled date
- `entry_time`: Optional time (important for meals, grocery shopping, meal prep)
- `grocery_list`: JSON object with shopping list items (for grocery_shopping entries)
- `prep_instructions`: JSON object with batch cooking instructions (for meal_prep entries)
- `completion_status`: Tracks lifecycle

**grocery_list JSONB Structure**:
```json
{
  "items": [
    {
      "ingredient": "Chicken breast",
      "quantity": "2 lbs",
      "category": "Meat",
      "notes": "boneless, skinless"
    },
    {
      "ingredient": "Brown rice",
      "quantity": "2 bags",
      "category": "Grains"
    }
  ],
  "shopping_date": "2025-12-15"
}
```

**prep_instructions JSONB Structure**:
```json
{
  "session_name": "Sunday Meal Prep",
  "duration_minutes": 120,
  "recipes": ["Grilled Chicken", "Brown Rice", "Roasted Vegetables"],
  "batch_size": 10,
  "instructions": [
    "1. Preheat oven to 400°F",
    "2. Season chicken breasts",
    "3. Cook rice according to package",
    "4. Roast vegetables for 20 minutes"
  ],
  "storage_instructions": "Store in airtight containers, refrigerate, use within 4 days"
}
```

**Validation Rules**:
- Exactly one of `workout_id`, `meal_id`, `grocery_list`, or `prep_instructions` must be set based on `entry_type`
- `completed_at` only set when `completion_status = 'completed'`

**Relationships**:
- Belongs to `Schedule`
- Optionally references `Workout` or `Meal`

---

### 11. ProgressRecord

Represents historical tracking data and milestones.

```sql
CREATE TABLE progress_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fitness_plan_id UUID REFERENCES fitness_plans(id) ON DELETE SET NULL,
    
    record_date DATE NOT NULL,
    record_type VARCHAR(50) NOT NULL,  -- daily_summary, milestone, measurement
    
    -- Completion stats
    workouts_completed_today INT DEFAULT 0,
    meals_completed_today INT DEFAULT 0,
    
    -- Measurements (optional, depends on record_type)
    weight_lbs DECIMAL(5,2),
    body_fat_percentage DECIMAL(4,2),
    measurements JSONB,  -- {"chest": 40, "waist": 32, "arms": 14}
    
    -- Calculated metrics
    weekly_adherence_rate DECIMAL(5,2),  -- Percentage
    total_workouts_completed INT,
    current_streak_days INT,
    
    -- Milestones
    milestone_achieved BOOLEAN DEFAULT FALSE,
    milestone_description TEXT,
    
    -- User input
    energy_level INT CHECK (energy_level BETWEEN 1 AND 10),
    mood VARCHAR(50),
    user_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_progress_records_user ON progress_records(user_id);
CREATE INDEX idx_progress_records_date ON progress_records(record_date);
CREATE INDEX idx_progress_records_user_date ON progress_records(user_id, record_date DESC);
CREATE INDEX idx_progress_records_type ON progress_records(record_type);
CREATE INDEX idx_progress_records_milestones ON progress_records(milestone_achieved) WHERE milestone_achieved = TRUE;
```

**Attributes**:
- `record_type`: daily_summary, milestone, measurement
- `weekly_adherence_rate`: Calculated completion percentage
- `current_streak_days`: Consecutive days with completed activities
- `milestone_achieved`: Boolean flag for important achievements

**Relationships**:
- Belongs to `User`
- Optionally belongs to `FitnessPlan`

---

### 12. Conversation

Represents interaction history between user and AI agent.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fitness_plan_id UUID REFERENCES fitness_plans(id) ON DELETE SET NULL,
    
    conversation_type VARCHAR(50) NOT NULL,  -- plan_creation, plan_modification, schedule_adjustment, general_query
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, abandoned
    
    -- Context
    conversation_context JSONB,  -- Stores conversation state, pending questions, etc.
    
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_fitness_plan ON conversations(fitness_plan_id);
CREATE INDEX idx_conversations_type ON conversations(conversation_type);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
```

**conversation_context JSONB Example**:
```json
{
  "intent": "create_plan",
  "collected_info": {
    "goal": "lose 15 pounds",
    "timeframe": "3 months",
    "current_fitness_level": "beginner",
    "equipment": ["home", "dumbbells"]
  },
  "pending_questions": [
    "dietary_preferences",
    "workout_frequency"
  ],
  "current_step": "gathering_preferences"
}
```

**Relationships**:
- Belongs to `User`
- Optionally associated with `FitnessPlan`
- Has many `Messages`
- Has many `DisruptionEvents`

---

### 13. Message

Represents a single message in a conversation.

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    sender_type VARCHAR(50) NOT NULL,  -- user, assistant, system
    message_content TEXT NOT NULL,
    
    -- AI metadata (for assistant messages)
    model_used VARCHAR(100),
    tokens_used INT,
    function_calls JSONB,  -- Which AI tools were called
    
    -- Timestamps
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_sent_at ON messages(sent_at);
CREATE INDEX idx_messages_conversation_time ON messages(conversation_id, sent_at);
```

**function_calls JSONB Example**:
```json
{
  "calls": [
    {
      "function": "get_current_plan",
      "arguments": {"user_id": "uuid"},
      "result_summary": "Retrieved active plan: Weight Loss Plan"
    },
    {
      "function": "reschedule_workouts",
      "arguments": {"user_id": "uuid", "days_affected": 3, "reason": "illness"},
      "result_summary": "Rescheduled 2 workouts, extended timeline by 3 days"
    }
  ]
}
```

**Relationships**:
- Belongs to `Conversation`

---

### 14. DisruptionEvent

Represents an unexpected obstruction reported by user.

```sql
CREATE TABLE disruption_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    fitness_plan_id UUID NOT NULL REFERENCES fitness_plans(id) ON DELETE CASCADE,
    
    disruption_type VARCHAR(50) NOT NULL,  -- illness, travel, injury, work_commitment, personal
    start_date DATE NOT NULL,
    end_date DATE,  -- NULL if ongoing
    
    description TEXT NOT NULL,
    severity VARCHAR(50),  -- minor, moderate, major
    
    -- Impact
    workouts_affected INT DEFAULT 0,
    meals_affected INT DEFAULT 0,
    
    -- Resolution
    resolution_strategy TEXT,  -- How schedule was adjusted
    timeline_extension_days INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_disruption_events_user ON disruption_events(user_id);
CREATE INDEX idx_disruption_events_fitness_plan ON disruption_events(fitness_plan_id);
CREATE INDEX idx_disruption_events_type ON disruption_events(disruption_type);
CREATE INDEX idx_disruption_events_dates ON disruption_events(start_date, end_date);
```

**Attributes**:
- `disruption_type`: Categorizes the disruption
- `severity`: Helps AI determine rescheduling strategy
- `resolution_strategy`: Documents how the disruption was handled
- `timeline_extension_days`: How much the plan was extended

**Relationships**:
- Belongs to `User`
- Belongs to `FitnessPlan`
- Optionally belongs to `Conversation`

---

## Database Indexes Summary

### Critical Indexes for Performance

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);

-- Fitness plan queries
CREATE INDEX idx_fitness_plans_user_status ON fitness_plans(user_id, current_status);
CREATE INDEX idx_fitness_plans_snapshot ON fitness_plans USING GIN (plan_snapshot);

-- Schedule queries (most frequent)
CREATE INDEX idx_schedule_entries_user_date ON schedule_entries(schedule_id, entry_date);
CREATE INDEX idx_schedule_entries_date ON schedule_entries(entry_date);
CREATE INDEX idx_schedule_entries_status ON schedule_entries(completion_status);

-- Progress tracking
CREATE INDEX idx_progress_records_user_date ON progress_records(user_id, record_date DESC);

-- Conversation queries
CREATE INDEX idx_messages_conversation_time ON messages(conversation_id, sent_at);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
```

### JSONB Indexes

```sql
-- GIN indexes for JSONB queries
CREATE INDEX idx_fitness_plans_snapshot ON fitness_plans USING GIN (plan_snapshot);
CREATE INDEX idx_exercises_muscle_groups ON exercises USING GIN (target_muscle_groups);
```

---

## State Transitions

### FitnessPlan Status
```
[created] → active → [completed | paused | abandoned]
                  ↑__________|
                   (resume)
```

### ScheduleEntry Status
```
scheduled → [completed | skipped | rescheduled]
```

### Phase Status
```
not_started → in_progress → completed
```

### Conversation Status
```
active → [completed | abandoned]
```

---

## Data Integrity Rules

1. **User Constraints**:
   - Only one active `FitnessPlan` per user at a time (application-level constraint)
   - Email must be unique
   - Password must never be stored in plaintext

2. **Fitness Plan Constraints**:
   - Each `FitnessPlan` must have exactly one `WorkoutPlan` and one `MealPlan`
   - `target_end_date` must be after `start_date`
   - `plan_snapshot` JSONB must be valid

3. **Schedule Constraints**:
   - Each `FitnessPlan` has exactly one `Schedule`
   - `ScheduleEntry` must reference either a workout or a meal, not both
   - No scheduling conflicts (two workouts at same time)

4. **Progress Constraints**:
   - `record_date` cannot be in the future
   - Adherence rates must be between 0 and 100

5. **Conversation Constraints**:
   - Messages must belong to a conversation
   - Message ordering preserved by timestamp

---

## Soft Delete Strategy

Only `users` table uses soft delete (via `deleted_at` column). All related entities use CASCADE delete to ensure data consistency when a user account is deleted.

For analytics purposes, consider archiving deleted user data before actual deletion.

---

## Migration Strategy

### Initial Schema Creation
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Adding Multi-Phase Support (Example Future Migration)
```python
# alembic/versions/002_add_phases.py
def upgrade():
    op.create_table(
        'phases',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('fitness_plan_id', UUID(), nullable=False),
        # ... other columns
    )
    op.add_column('workouts', sa.Column('phase_id', UUID(), nullable=True))
    op.add_column('meals', sa.Column('phase_id', UUID(), nullable=True))

def downgrade():
    op.drop_column('meals', 'phase_id')
    op.drop_column('workouts', 'phase_id')
    op.drop_table('phases')
```

---

## JSONB vs Normalized Approach

**JSONB is used for**:
- AI-generated plan snapshots (flexible structure, versioned)
- Conversation context (evolving state)
- Exercise alternatives (array of UUIDs)
- User preferences (variable settings)

**Normalized tables are used for**:
- Core entities (users, plans, workouts)
- Scheduling (needs efficient date queries)
- Progress tracking (requires aggregations)
- Relationships (referential integrity)

This hybrid approach balances flexibility (JSONB) with performance and data integrity (normalized tables).

---

## Query Examples

### Get Today's Schedule
```sql
SELECT 
    se.*,
    w.name as workout_name,
    m.name as meal_name
FROM schedule_entries se
LEFT JOIN workouts w ON se.workout_id = w.id
LEFT JOIN meals m ON se.meal_id = m.id
WHERE se.schedule_id = (
    SELECT id FROM schedules WHERE user_id = $1 AND fitness_plan_id = (
        SELECT id FROM fitness_plans WHERE user_id = $1 AND current_status = 'active' LIMIT 1
    )
)
AND se.entry_date = CURRENT_DATE
ORDER BY se.entry_time NULLS LAST;
```

### Calculate Weekly Adherence
```sql
WITH weekly_schedule AS (
    SELECT COUNT(*) as total_scheduled
    FROM schedule_entries
    WHERE schedule_id = $1
    AND entry_date >= CURRENT_DATE - INTERVAL '7 days'
    AND entry_date <= CURRENT_DATE
),
weekly_completed AS (
    SELECT COUNT(*) as total_completed
    FROM schedule_entries
    WHERE schedule_id = $1
    AND entry_date >= CURRENT_DATE - INTERVAL '7 days'
    AND entry_date <= CURRENT_DATE
    AND completion_status = 'completed'
)
SELECT 
    (weekly_completed.total_completed::FLOAT / weekly_schedule.total_scheduled * 100) as adherence_rate
FROM weekly_schedule, weekly_completed;
```

### Get Current Phase
```sql
SELECT *
FROM phases
WHERE fitness_plan_id = $1
AND CURRENT_DATE BETWEEN start_date AND end_date
LIMIT 1;
```

---

## Summary

This data model supports all functional requirements:

- ✅ **FR-001 to FR-008**: Plan creation and management
- ✅ **FR-009 to FR-015**: Scheduling and tracking
- ✅ **FR-016 to FR-020**: Adaptability and rescheduling (via DisruptionEvent)
- ✅ **FR-021 to FR-027**: AI interaction (via Conversation, Message, JSONB for tool calls)
- ✅ **FR-028 to FR-034**: User preferences (User table, arrays for preferences)
- ✅ **FR-035 to FR-039**: Progress tracking (ProgressRecord)
- ✅ **FR-040 to FR-043**: Data persistence and user management

The model balances:
- **Performance**: Efficient indexes, caching-friendly structure
- **Flexibility**: JSONB for AI-generated content
- **Data Integrity**: Foreign keys, constraints, validation
- **Scalability**: UUID primary keys, partition-ready date columns
- **Constitutional Compliance**: Type safety, explicit relationships, documented constraints
