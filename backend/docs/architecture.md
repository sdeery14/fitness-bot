# Architecture Documentation - AI-Powered Fitness Planner

**Version**: 1.0  
**Last Updated**: November 17, 2025

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Multi-Agent AI System](#multi-agent-ai-system)
4. [Technology Stack](#technology-stack)
5. [Data Model](#data-model)
6. [Application Layers](#application-layers)
7. [Data Flow](#data-flow)
8. [External Integrations](#external-integrations)
9. [Deployment Architecture](#deployment-architecture)
10. [Security Architecture](#security-architecture)
11. [Performance Considerations](#performance-considerations)

---

## Overview

The AI-Powered Fitness Planner is a full-stack web application that enables users to create, follow, and adapt personalized fitness plans through conversational AI. The system uses a sophisticated multi-agent architecture to generate comprehensive fitness plans that include both workout routines and meal plans, while maintaining a dynamic schedule that adapts to user disruptions and progress.

**Core Capabilities**:
- Conversational AI-powered fitness plan generation
- Multi-phase, long-term plan support (weeks to multi-year)
- Daily schedule management with workout and meal tracking
- Intelligent rescheduling for disruptions (illness, travel, commitments)
- Progress tracking with body measurements and adherence statistics
- Real-time streaming AI responses via Server-Sent Events (SSE)

**Key Design Principles**:
- **Scalability**: Stateless JWT authentication, horizontal scaling support, async task processing
- **Maintainability**: Modular multi-agent design, clear separation of concerns, comprehensive type hints
- **Performance**: Parallel agent execution, Redis caching, streaming responses, optimistic UI updates
- **Reliability**: Background task processing with Celery, database transactions, error recovery

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend (Next.js)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │  Dashboard   │  │  AI Chat     │  │  Schedule    │  │  Progress   ││
│  │              │  │  Interface   │  │  Tracker     │  │  Tracking   ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘│
│           │                │                 │                │         │
│           └────────────────┴─────────────────┴────────────────┘         │
│                                     │                                    │
└─────────────────────────────────────┼────────────────────────────────────┘
                                      │ HTTP/REST + SSE
                                      ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                               │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                        API Layer (Routers)                         ││
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐││
│  │  │  Auth   │  │  Users  │  │  Plans   │  │ Schedule │  │Progress│││
│  │  └─────────┘  └─────────┘  └──────────┘  └──────────┘  └────────┘││
│  │         │            │            │             │            │      ││
│  └─────────┼────────────┼────────────┼─────────────┼────────────┼──────┘│
│            │            │            │             │            │       │
│  ┌─────────┴────────────┴────────────┴─────────────┴────────────┴──────┐│
│  │                       Service Layer                                 ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ ││
│  │  │   Auth      │  │    User     │  │     Plan     │  │Conversation││
│  │  │  Service    │  │   Service   │  │   Service    │  │  Service  │ ││
│  │  └─────────────┘  └─────────────┘  └──────────────┘  └──────────┘ ││
│  │         │                 │                 │                │      ││
│  │         │                 │                 ↓                │      ││
│  │         │                 │      ┌───────────────────┐       │      ││
│  │         │                 │      │ AI Orchestration  │←──────┘      ││
│  │         │                 │      │     Service       │              ││
│  │         │                 │      └────────┬──────────┘              ││
│  │         │                 │               │                         ││
│  └─────────┼─────────────────┼───────────────┼─────────────────────────┘│
│            │                 │               │                          │
│  ┌─────────┴─────────────────┴───────────────┴─────────────────────────┐│
│  │                      Multi-Agent AI System                          ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐││
│  │  │Conversation  │  │ Fitness Plan │  │ Workout Plan │  │  Meal   │││
│  │  │   Agent      │→ │    Agent     │→ │    Agent     │  │  Plan   │││
│  │  │  (Triage)    │  │ (Orchestrate)│  │ (Specialist) │  │ Agent   │││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘││
│  │         │                 │                 │                │      ││
│  └─────────┼─────────────────┼─────────────────┼────────────────┼──────┘│
│            │                 │                 │                │       │
│  ┌─────────┴─────────────────┴─────────────────┴────────────────┴──────┐│
│  │                      Data Access Layer                              ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             ││
│  │  │ PostgreSQL   │  │    Redis     │  │   External   │             ││
│  │  │  (Primary)   │  │   (Cache)    │  │   APIs       │             ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘             ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                   Background Processing (Celery)                    ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             ││
│  │  │  Schedule    │  │ Notifications│  │Phase Transition│            ││
│  │  │Recalculation │  │              │  │               │             ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘             ││
│  └─────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

### Architecture Layers

**Frontend Layer (Next.js + TypeScript)**:
- Server-side rendering (SSR) for SEO and performance
- Client-side state management with Zustand
- Real-time updates via SSE connections
- Optimistic UI updates for immediate feedback
- Responsive design with Tailwind CSS and shadcn/ui components

**API Layer (FastAPI Routers)**:
- RESTful endpoints for CRUD operations
- SSE streaming for AI conversations
- JWT authentication middleware
- Request validation with Pydantic schemas
- Rate limiting middleware

**Service Layer**:
- Business logic encapsulation
- Transaction management
- AI orchestration coordination
- External API integration
- Data transformation and validation

**Multi-Agent AI System**:
- OpenAI Agents SDK for agent framework
- Conversation management and routing
- Parallel specialist agent execution
- State persistence via Redis and PostgreSQL
- Streaming response generation

**Data Layer**:
- PostgreSQL for relational data persistence
- Redis for session state and caching
- SQLAlchemy ORM with async support
- Alembic for database migrations

**Background Processing (Celery)**:
- Asynchronous task execution
- Scheduled jobs (daily schedule generation)
- Long-running operations (plan recalculation)
- Email/notification delivery

---

## Multi-Agent AI System

The core innovation of this application is the **multi-agent architecture** that orchestrates specialized AI agents for different aspects of fitness plan generation.

### Agent Architecture

```
User Request
    ↓
┌────────────────────────────────────────────────────────┐
│        Conversation Agent (Triage Agent)              │
│  • Extracts user requirements                         │
│  • Asks clarifying questions                          │
│  • Manages conversation state                         │
│  • Routes to specialist agents                        │
└────────────────┬───────────────────────────────────────┘
                 │ [User Info + Goal]
                 ↓
┌────────────────────────────────────────────────────────┐
│         Fitness Plan Agent (Orchestrator)             │
│  • Coordinates overall plan structure                 │
│  • Determines phases and duration                     │
│  • Delegates to specialist agents                     │
│  • Synthesizes final plan                             │
└────────────┬───────────────────────────┬───────────────┘
             │                           │
             │ [Handoff]                 │ [Handoff]
             ↓                           ↓
┌───────────────────────┐    ┌────────────────────────┐
│ Workout Plan Agent    │    │  Meal Plan Agent       │
│  • Selects exercises  │    │  • Generates meals     │
│  • Creates routines   │    │  • Calculates macros   │
│  • Sets progression   │    │  • Uses USDA data      │
│  • Uses curated DB    │    │  • Balances nutrition  │
└───────────┬───────────┘    └────────┬───────────────┘
            │                         │
            │ [Workout Plan]          │ [Meal Plan]
            ↓                         ↓
┌────────────────────────────────────────────────────────┐
│         Fitness Plan Agent (Synthesis)                │
│  • Combines workout + meal plans                      │
│  • Stores complete plan in database                   │
│  • Returns to user via streaming response             │
└────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

#### 1. Conversation Agent (Triage Agent)
**Model**: GPT-4o (balanced preset)  
**Temperature**: 0.7  
**Purpose**: First point of contact, requirement gathering

**Capabilities**:
- Extracts user's fitness goal (weight loss, muscle gain, endurance, etc.)
- Asks clarifying questions (current fitness level, equipment access, dietary restrictions)
- Manages conversation flow and context
- Detects when enough information is gathered
- Routes to Fitness Plan Agent for plan generation

**Context Management**:
- Stores conversation history in database (PostgreSQL)
- Tracks user profile data (preferences, restrictions, goals)
- Uses Redis for session state during active conversations

**Example Interaction**:
```
User: "I want to lose 15 pounds in 3 months"
Agent: "Great goal! To create the perfect plan for you, I have a few questions:
        1. What's your current fitness level? (beginner/intermediate/advanced)
        2. Do you have access to a gym or prefer home workouts?
        3. Any dietary restrictions I should know about?"
```

#### 2. Fitness Plan Agent (Orchestrator)
**Model**: GPT-4o (quality preset)  
**Temperature**: 0.5  
**Purpose**: High-level plan structure and coordination

**Capabilities**:
- Determines plan duration and phase structure
- Calculates workout frequency based on goals
- Coordinates parallel handoffs to specialist agents
- Synthesizes workout and meal plans into cohesive fitness plan
- Ensures plan alignment with user's goals and constraints

**Orchestration Flow**:
1. Receives user context from Conversation Agent
2. Determines plan parameters (duration, phases, intensity)
3. **Parallel handoffs**: Simultaneously delegates to Workout Plan Agent and Meal Plan Agent
4. Waits for specialist responses
5. Combines workout plan + meal plan into final fitness plan
6. Persists plan to database and returns to user

**Performance Optimization**:
- Parallel agent execution reduces total generation time by ~50%
- Uses storage references (database IDs) instead of passing full data to LLMs
- Streams progress updates to frontend during generation

#### 3. Workout Plan Agent (Specialist)
**Model**: GPT-4o (creative preset)  
**Temperature**: 1.0  
**Purpose**: Generate workout routines and exercise selection

**Capabilities**:
- Selects exercises from curated database (200-500 exercises)
- Creates weekly workout routines
- Sets progression strategy (progressive overload, periodization)
- Balances muscle groups and recovery
- Adapts to equipment availability
- Provides alternatives for injured/limited users

**Data Sources**:
- **Exercise Database**: Curated collection with attributes:
  - Muscle groups targeted (primary, secondary)
  - Equipment required (none, dumbbells, barbell, gym, etc.)
  - Difficulty level (beginner, intermediate, advanced)
  - Movement patterns (push, pull, squat, hinge, carry)
  - Exercise alternatives for progression/regression

**Example Output**:
```json
{
  "workout_plan": {
    "frequency_per_week": 4,
    "progression_strategy": "Progressive overload with 5% increases every 2 weeks",
    "workouts": [
      {
        "name": "Upper Body Push",
        "type": "strength",
        "duration_minutes": 45,
        "exercises": [
          {
            "exercise_id": "db_123",
            "name": "Barbell Bench Press",
            "sets": 4,
            "reps": "8-10",
            "rest_seconds": 90,
            "notes": "Focus on controlled eccentric"
          }
        ]
      }
    ]
  }
}
```

#### 4. Meal Plan Agent (Specialist)
**Model**: GPT-4o (creative preset)  
**Temperature**: 1.0  
**Purpose**: Generate meal plans with accurate nutritional data

**Capabilities**:
- Calculates daily calorie targets based on goal (deficit, surplus, maintenance)
- Determines macronutrient ratios (protein, carbs, fats)
- Generates meal suggestions using USDA FoodData Central API
- Respects dietary restrictions (vegetarian, vegan, allergies, religious)
- Provides variety across days and weeks
- Balances nutrition across all meals

**Data Sources**:
- **USDA FoodData Central API**: 
  - 300,000+ food items with detailed nutrition data
  - Accurate macros and micronutrients
  - Ingredient-level filtering for restrictions
  - Portion size calculations

**Macro Calculation Example**:
```python
# Weight loss goal: 500 calorie deficit
BMR = 1800 (calculated from user profile)
TDEE = BMR * activity_multiplier = 2400
Target_calories = TDEE - 500 = 1900

# Macro split for muscle preservation:
Protein = 1g per lb body weight = 180g = 720 cal (38%)
Fat = 0.4g per lb = 72g = 648 cal (34%)
Carbs = remaining = 133g = 532 cal (28%)
```

**Example Output**:
```json
{
  "meal_plan": {
    "daily_calorie_target": 1900,
    "macros": {
      "protein_grams": 180,
      "carbs_grams": 133,
      "fat_grams": 72
    },
    "meals": [
      {
        "name": "Grilled Chicken Salad",
        "meal_type": "lunch",
        "calories": 450,
        "protein_grams": 40,
        "carbs_grams": 30,
        "fat_grams": 18,
        "ingredients": [
          {
            "food_id": "usda_12345",
            "name": "Chicken breast, grilled",
            "amount": 6,
            "unit": "oz"
          }
        ]
      }
    ]
  }
}
```

### Agent Communication & State Management

**Session Management**:
- Each conversation has a unique `session_id` stored in database
- OpenAI Agents SDK automatically manages conversation history within sessions
- Session state cached in Redis for fast access during active conversations

**Context Passing**:
```python
# User context passed to all agents
class UserContext:
    user_id: str
    email: str
    preferences: dict  # dietary restrictions, equipment, schedule

# Plan context for specialist agents
class PlanContext:
    goal_description: str
    duration_weeks: int
    fitness_level: str
    workout_frequency: int
```

**Storage References Over Data Passing**:
- Agents receive database IDs and Redis keys, not full objects
- Reduces token usage and improves performance
- Example: Pass `exercise_db_key: "exercises:strength:upper"` instead of full exercise list

**Parallel Execution**:
```python
# Pseudo-code for orchestration
async def generate_plan(user_context: UserContext) -> FitnessPlan:
    # Fitness Plan Agent coordinates
    plan_params = fitness_plan_agent.determine_structure(user_context)
    
    # Parallel handoffs to specialists
    workout_task = workout_agent.generate_plan(plan_params)
    meal_task = meal_agent.generate_plan(plan_params)
    
    # Wait for both (runs concurrently)
    workout_plan, meal_plan = await asyncio.gather(workout_task, meal_task)
    
    # Synthesize and persist
    fitness_plan = fitness_plan_agent.synthesize(workout_plan, meal_plan)
    await db.save(fitness_plan)
    
    return fitness_plan
```

### Agent Model Configuration

**Model Presets** (defined in `backend/src/ai/agent.py`):

| Preset | Model | Temperature | Max Tokens | Use Case |
|--------|-------|-------------|------------|----------|
| `fast` | gpt-4o-mini | 0.7 | 1000 | Simple responses, status updates |
| `balanced` | gpt-4o | 0.7 | 2000 | Conversation Agent (default) |
| `quality` | gpt-4o | 0.5 | 4000 | Fitness Plan Agent (orchestration) |
| `creative` | gpt-4o | 1.0 | 2000 | Workout/Meal Plan Agents (variety) |

**Why Different Temperatures**:
- **Lower (0.5)** for orchestration: Ensures consistent, logical plan structure
- **Higher (1.0)** for specialists: Encourages variety in exercise/meal selection
- **Balanced (0.7)** for conversation: Natural but focused dialogue

---

## Technology Stack

### Backend

**Core Framework**:
- **FastAPI 0.109+**: Modern async web framework
  - Built-in OpenAPI documentation
  - Async/await support for I/O operations
  - Pydantic integration for validation

**Database & ORM**:
- **PostgreSQL 15+**: Primary data store
  - ACID compliance for transactional integrity
  - JSON/JSONB support for flexible schema (plan snapshots)
  - Full-text search capabilities (future: exercise/meal search)
- **SQLAlchemy 2.0+**: ORM with async support
  - Type-safe query building
  - Relationship management
  - Automatic migrations with Alembic

**Caching & Session Storage**:
- **Redis 7+**: In-memory data store
  - Session state caching
  - Rate limiting counters
  - Temporary data storage during plan generation

**AI & ML**:
- **OpenAI Agents SDK**: Multi-agent orchestration framework
  - Automatic conversation history management
  - Tool/function calling support
  - Streaming response generation
- **OpenAI API (GPT-4o)**: Language model provider

**Background Processing**:
- **Celery 5+**: Distributed task queue
  - Async plan generation
  - Scheduled jobs (daily schedule creation)
  - Email/notification delivery
- **Redis**: Message broker and result backend for Celery

**External APIs**:
- **USDA FoodData Central API**: Nutritional data
  - 300,000+ food items
  - Detailed macro/micronutrient information

### Frontend

**Framework & Language**:
- **Next.js 14+**: React framework with SSR/SSG
  - App Router for modern routing
  - Server Components for performance
  - API routes for BFF pattern
- **TypeScript 5+**: Type-safe development
  - Enhanced IDE support
  - Compile-time error detection

**State Management**:
- **Zustand**: Lightweight state management
  - Simple API, minimal boilerplate
  - Excellent TypeScript support
  - DevTools integration

**UI Components**:
- **Tailwind CSS 3+**: Utility-first styling
- **shadcn/ui**: Accessible component library
  - Built on Radix UI primitives
  - Customizable and composable
  - WCAG 2.1 Level AA compliant

**Real-Time Communication**:
- **EventSource API**: SSE client for streaming
  - Native browser support
  - Automatic reconnection
  - Efficient for one-way server→client updates

### DevOps & Infrastructure

**Containerization**:
- **Docker**: Application containerization
- **Docker Compose**: Multi-container orchestration

**CI/CD**:
- **GitHub Actions**: Automated testing and deployment
- **Pre-commit hooks**: Code quality enforcement

**Testing**:
- **pytest**: Backend unit and integration tests
- **Vitest**: Frontend unit tests
- **Playwright**: E2E testing

**Code Quality**:
- **Ruff**: Fast Python linter/formatter
- **ESLint + Prettier**: TypeScript/JavaScript linting
- **mypy**: Static type checking for Python

---

## Data Model

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌──────────┐                                                          │
│  │   User   │                                                          │
│  ├──────────┤                                                          │
│  │ id (PK)  │                                                          │
│  │ email    │                                                          │
│  │ password │                                                          │
│  │ profile  │                                                          │
│  └────┬─────┘                                                          │
│       │ 1                                                              │
│       │                                                                │
│       │ *                                                              │
│  ┌────┴────────────┐                                                  │
│  │  FitnessPlan    │                                                  │
│  ├─────────────────┤                                                  │
│  │ id (PK)         │                                                  │
│  │ user_id (FK)    │                                                  │
│  │ goal_type       │                                                  │
│  │ duration_weeks  │                                                  │
│  │ current_phase   │                                                  │
│  │ status          │────┐                                            │
│  │ plan_snapshot   │    │                                            │
│  └────┬────────────┘    │                                            │
│       │ 1               │ 1                                          │
│       │                 │                                            │
│       │ 1               │ 1                                          │
│  ┌────┴──────────┐  ┌──┴──────────────┐                             │
│  │ WorkoutPlan   │  │   MealPlan      │                             │
│  ├───────────────┤  ├─────────────────┤                             │
│  │ id (PK)       │  │ id (PK)         │                             │
│  │ plan_id (FK)  │  │ plan_id (FK)    │                             │
│  │ frequency     │  │ daily_calories  │                             │
│  │ progression   │  │ macros          │                             │
│  └────┬──────────┘  └──┬──────────────┘                             │
│       │ 1              │ 1                                           │
│       │                │                                             │
│       │ *              │ *                                           │
│  ┌────┴───────┐   ┌───┴────┐                                        │
│  │  Workout   │   │  Meal  │                                        │
│  ├────────────┤   ├────────┤                                        │
│  │ id (PK)    │   │ id(PK) │                                        │
│  │ name       │   │ name   │                                        │
│  │ type       │   │ type   │                                        │
│  │ exercises  │   │ macros │                                        │
│  └────┬───────┘   └───┬────┘                                        │
│       │               │                                             │
│       │               │                                             │
│  ┌────┴───────────────┴────┐                                        │
│  │      Schedule           │                                        │
│  ├─────────────────────────┤                                        │
│  │ id (PK)                 │                                        │
│  │ plan_id (FK)            │                                        │
│  │ entry_date              │                                        │
│  │ entry_type (workout/meal)│                                       │
│  │ status (scheduled/complete)│                                     │
│  │ workout_id (FK, nullable)│                                       │
│  │ meal_id (FK, nullable)   │                                       │
│  └─────────────────────────┘                                        │
│                                                                      │
│  ┌──────────────┐                                                   │
│  │ Conversation │                                                   │
│  ├──────────────┤                                                   │
│  │ id (PK)      │                                                   │
│  │ user_id (FK) │                                                   │
│  │ session_id   │                                                   │
│  │ type         │                                                   │
│  │ status       │                                                   │
│  └────┬─────────┘                                                   │
│       │ 1                                                           │
│       │                                                             │
│       │ *                                                           │
│  ┌────┴─────────┐                                                   │
│  │   Message    │                                                   │
│  ├──────────────┤                                                   │
│  │ id (PK)      │                                                   │
│  │ conv_id (FK) │                                                   │
│  │ sender_type  │                                                   │
│  │ content      │                                                   │
│  │ created_at   │                                                   │
│  └──────────────┘                                                   │
│                                                                      │
│  ┌──────────────┐                                                   │
│  │   Progress   │                                                   │
│  ├──────────────┤                                                   │
│  │ id (PK)      │                                                   │
│  │ user_id (FK) │                                                   │
│  │ plan_id (FK) │                                                   │
│  │ record_type  │ (weight, body_fat, circumference)                │
│  │ value        │                                                   │
│  │ record_date  │                                                   │
│  └──────────────┘                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Tables

**User**: Authentication and profile data
- Stores hashed passwords (bcrypt)
- Contains user preferences (dietary restrictions, equipment, timezone)
- Linked to all user-generated content

**FitnessPlan**: Core plan entity
- `plan_snapshot`: JSONB field storing AI-generated plan structure
- `current_status`: Enum (active, paused, completed, abandoned)
- `current_phase_number`: Tracks progression through multi-phase plans

**WorkoutPlan & Workout**: Exercise routines
- WorkoutPlan: Overall strategy and frequency
- Workout: Individual workout sessions with exercise details

**MealPlan & Meal**: Nutrition planning
- MealPlan: Daily calorie targets and macro ratios
- Meal: Individual meals with USDA nutrition data

**Schedule**: Daily schedule management
- Polymorphic relationship to Workout OR Meal via `entry_type`
- Tracks completion status and timestamps

**Conversation & Message**: AI chat history
- Conversation: Session-level container
- Message: Individual user/assistant messages with timestamps

**Progress**: Measurement tracking
- Body weight, body fat %, circumferences
- Time-series data for visualization

---

## Application Layers

### 1. API Layer (`backend/src/api/`)

**Routers**:
- `auth.py`: Registration, login, token refresh
- `users.py`: Profile management
- `fitness_plans.py`: CRUD operations for plans
- `schedules.py`: Daily schedule queries, completion tracking
- `progress.py`: Measurement recording and retrieval
- `ai_agent.py`: AI conversation endpoints, SSE streaming

**Middleware**:
- `auth_middleware.py`: JWT token validation, user injection
- `rate_limiting.py`: Request throttling per endpoint category
- `error_handlers.py`: Centralized exception handling

### 2. Service Layer (`backend/src/services/`)

**Core Services**:
- `auth_service.py`: Password hashing, token generation/validation
- `user_service.py`: User CRUD, preference management
- `plan_service.py`: Plan creation, phase transitions, timeline calculations
- `conversation_service.py`: Chat history persistence, session management
- `ai_service.py`: AI orchestration, agent coordination, streaming

**Responsibilities**:
- Business logic implementation
- Transaction boundaries
- Cross-entity coordination
- External API integration

### 3. AI Layer (`backend/src/ai/`)

**Core Modules**:
- `agent.py`: Base agent configuration, model presets, context models
- `app_agents/conversation_agent.py`: Triage agent implementation
- `app_agents/fitness_plan_agent.py`: Orchestration agent with handoffs
- `app_agents/workout_plan_agent.py`: Exercise selection specialist
- `app_agents/meal_plan_agent.py`: Nutrition planning specialist
- `schemas.py`: Pydantic models for agent outputs

**Agent Registry**:
- Centralized agent management
- Lazy initialization for performance
- Singleton pattern for shared agents

### 4. Data Layer (`backend/src/models/`)

**ORM Models**:
- SQLAlchemy models with mixins (UUIDMixin, TimestampMixin)
- Relationships configured with lazy loading strategies
- Custom types for enums (GoalType, FitnessLevel, etc.)

**Database Configuration**:
- Async session factory for concurrent requests
- Connection pooling with configurable limits
- Transaction isolation level: READ COMMITTED

### 5. Background Tasks (`backend/src/background/`)

**Celery Tasks**:
- `schedule_recalc.py`: Recalculate schedule after disruptions
- `notifications.py`: Email delivery, in-app notifications
- `phase_transitions.py`: Automatic phase advancement
- `plan_generation.py`: Async AI plan generation

**Scheduling**:
- Daily cron jobs for schedule generation
- Periodic cleanup of expired sessions
- Weekly progress report generation

---

## Data Flow

### Scenario 1: User Creates Fitness Plan

```
1. User sends initial message via frontend
   Frontend: POST /api/v1/ai/conversations
   ↓
2. API Layer validates request, authenticates user
   Router: ai_agent.py → start_conversation()
   ↓
3. Service Layer initiates AI orchestration
   AIOrchestrationService.start_conversation()
   ↓
4. Conversation Agent processes request
   - Extracts goal and user info
   - Asks clarifying questions
   - Stores message in database
   ↓
5. Frontend connects to SSE stream
   GET /api/v1/ai/conversations/{id}/stream
   ↓
6. User answers questions via messages
   POST /api/v1/ai/conversations/{id}/messages
   ↓
7. When ready, Fitness Plan Agent activates
   - Determines plan structure (phases, duration)
   - Parallel handoffs to Workout & Meal agents
   ↓
8. Specialist agents generate content
   [Parallel execution]
   - Workout Plan Agent: Queries exercise DB, creates routines
   - Meal Plan Agent: Queries USDA API, generates meals
   ↓
9. Fitness Plan Agent synthesizes results
   - Combines workout + meal plans
   - Creates FitnessPlan entity
   - Persists to PostgreSQL
   ↓
10. Response streamed to frontend
    SSE events: message_chunk → message_complete → plan_generated
    ↓
11. Frontend updates UI, navigates to plan view
```

### Scenario 2: User Marks Workout Complete

```
1. User taps "Mark Complete" button
   Frontend: Optimistic update (immediate UI change)
   POST /api/v1/schedules/entries/{id}/complete
   ↓
2. API Layer validates ownership and status
   Router: schedules.py → complete_entry()
   ↓
3. Service Layer updates database
   - Sets status = 'completed', completed_at = now()
   - Increments adherence counters
   - Triggers progress calculations
   ↓
4. Background task checks for achievements
   Celery: Check if milestone reached (streak, first week, etc.)
   ↓
5. Success response returned
   Frontend confirms optimistic update
   ↓
6. (If error) Frontend rolls back optimistic update
```

### Scenario 3: User Reports Disruption

```
1. User describes disruption via AI chat
   "I'll be sick for the next 3 days"
   POST /api/v1/ai/reschedule
   ↓
2. API Layer captures disruption details
   - type: illness
   - severity: moderate
   - start_date: today
   - end_date: +3 days
   ↓
3. Service Layer initiates rescheduling
   PlanService.handle_disruption()
   ↓
4. Background task recalculates schedule
   Celery: schedule_recalc.apply_async()
   - Shifts workouts to future dates
   - Adjusts phase timelines
   - Recalculates target end date
   ↓
5. AI generates adaptation summary
   - Explains changes
   - Provides recovery recommendations
   - Updates user via notification
   ↓
6. Updated schedule persisted to database
   ↓
7. Frontend polls for updated schedule
   GET /api/v1/schedules/upcoming
   Displays adjusted dates and AI reasoning
```

---

## External Integrations

### USDA FoodData Central API

**Purpose**: Accurate nutritional data for meal planning

**Integration Points**:
- `backend/src/integrations/usda_fooddata.py`
- Used by Meal Plan Agent during plan generation

**Key Operations**:
- Search food items by name/description
- Retrieve detailed nutrition for specific food IDs
- Calculate portion sizes for target macros

**Data Cached**:
- Common food items cached in Redis (1 week TTL)
- Reduces API calls and improves response time

**Rate Limits**:
- 1000 requests per hour (free tier)
- Implement request batching and caching

**API Key Configuration**:
- `USDA_API_KEY` environment variable
- Stored in `.env` file (not committed)

### Exercise Database

**Purpose**: Curated exercise library for workout planning

**Implementation**:
- **Current**: Seed data in `backend/data/exercises.json`
- **Future**: Could integrate with ExerciseDB API or JEFIT API

**Data Structure**:
```json
{
  "id": "ex_001",
  "name": "Barbell Bench Press",
  "category": "strength",
  "primary_muscles": ["chest"],
  "secondary_muscles": ["triceps", "shoulders"],
  "equipment": ["barbell", "bench"],
  "difficulty": "intermediate",
  "movement_pattern": "push",
  "alternatives": ["ex_002", "ex_003"],
  "instructions": "...",
  "video_url": "https://..."
}
```

---

## Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer (AWS ALB)                │
│                    HTTPS, SSL Termination                   │
└────────────────┬────────────────────────────┬───────────────┘
                 │                            │
                 ↓                            ↓
┌────────────────────────────┐  ┌────────────────────────────┐
│  Frontend (Next.js)        │  │  Backend (FastAPI)         │
│  ECS Fargate Tasks (2+)    │  │  ECS Fargate Tasks (3+)    │
│  - Auto-scaling on CPU     │  │  - Auto-scaling on requests│
│  - Health checks           │  │  - Health checks           │
└────────────────────────────┘  └────────┬───────────────────┘
                                         │
                                         ↓
                            ┌────────────────────────────────┐
                            │  Celery Workers                │
                            │  ECS Fargate Tasks (2+)        │
                            │  - Background processing       │
                            │  - Scheduled tasks             │
                            └────────────────────────────────┘
                                         │
                 ┌───────────────────────┼───────────────────┐
                 ↓                       ↓                   ↓
┌────────────────────────┐  ┌───────────────────┐  ┌────────────────┐
│ PostgreSQL             │  │  Redis             │  │  S3            │
│ RDS (Multi-AZ)         │  │  ElastiCache       │  │  Static Assets │
│ - Automated backups    │  │  - Session state   │  │  - Exercise DB │
│ - Read replicas        │  │  - Caching         │  │  - User uploads│
└────────────────────────┘  └───────────────────┘  └────────────────┘
```

### Environment Variables

**Required**:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key
- `JWT_SECRET`: Secret for JWT signing
- `USDA_API_KEY`: USDA FoodData API key

**Optional**:
- `CELERY_BROKER_URL`: Celery broker (defaults to REDIS_URL)
- `ENVIRONMENT`: development/staging/production
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR

### Docker Compose (Development)

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, redis]
    
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    
  db:
    image: postgres:15
    volumes: [postgres_data:/var/lib/postgresql/data]
    
  redis:
    image: redis:7-alpine
    
  celery_worker:
    build: ./backend
    command: celery -A src.background.celery_app worker
    depends_on: [redis, db]
```

---

## Security Architecture

### Authentication & Authorization

**JWT Tokens**:
- Access tokens: 24-hour expiration
- Refresh tokens: 30-day expiration
- HS256 algorithm with strong secret key
- Token payload includes user ID only (minimal PII)

**Password Security**:
- bcrypt hashing with cost factor 12
- Minimum 8 characters, complexity requirements enforced
- No password reuse across accounts (future: password history)

**Authorization**:
- User-scoped resources verified at service layer
- Foreign key relationships enforce ownership
- Admin role for future management features

### Data Protection

**Encryption**:
- In-transit: TLS 1.3 for all connections
- At-rest: RDS encryption, encrypted EBS volumes
- Sensitive fields: Consider encrypting API keys, PII in database

**Rate Limiting**:
- Auth endpoints: 5 requests/minute
- General API: 100 requests/minute
- AI streaming: 10 requests/minute
- Implemented via Redis counters with sliding windows

**Input Validation**:
- Pydantic schemas validate all request bodies
- SQL injection prevention via ORM parameterization
- XSS protection via content escaping

### GDPR & Privacy

**Data Retention**:
- User can request data export (JSON format)
- User can request account deletion (soft delete with 30-day grace period)
- Conversation history retained for 90 days by default

**Anonymization**:
- Progress data anonymized for analytics
- No PII shared with OpenAI (only fitness metrics, no names/emails)

---

## Performance Considerations

### Backend Optimizations

**Async I/O**:
- All database queries use async SQLAlchemy
- HTTP client uses httpx async
- Concurrent agent execution with asyncio.gather()

**Caching Strategy**:
- User profile cached in Redis (15-minute TTL)
- Exercise database cached (1-week TTL)
- USDA food data cached (1-week TTL)
- Schedule queries cached per user per day

**Database Indexing**:
- Indexes on foreign keys (user_id, plan_id, conversation_id)
- Composite index on (user_id, entry_date) for schedule queries
- Index on (conversation_id, created_at) for message retrieval

**Connection Pooling**:
- PostgreSQL: Max 20 connections per backend instance
- Redis: Connection pool with min 5, max 10 connections

### Frontend Optimizations

**Code Splitting**:
- Dynamic imports for route-level chunks
- Separate bundle for AI chat components

**Image Optimization**:
- Next.js Image component with automatic WebP conversion
- Lazy loading for below-fold content

**State Management**:
- Zustand slices prevent unnecessary re-renders
- Optimistic UI updates for immediate feedback
- Stale-while-revalidate pattern for data fetching

**SSE Connection Management**:
- Single EventSource per conversation
- Automatic reconnection with exponential backoff
- Heartbeat mechanism to detect dead connections

### AI Performance

**Token Optimization**:
- Storage references instead of full data in prompts
- Structured outputs reduce parsing overhead
- Parallel agent execution reduces total latency

**Streaming**:
- Incremental response delivery via SSE
- User sees progress instead of waiting for complete response
- Reduces perceived latency from 30s to <5s

**Caching**:
- Similar queries cached for 5 minutes (e.g., "lose 20 pounds in 3 months")
- Exercise selection cached by goal type

---

## Monitoring & Observability

**Logging**:
- Structured JSON logging with correlation IDs
- Log levels: DEBUG (dev), INFO (staging/prod)
- Centralized log aggregation (future: CloudWatch/Datadog)

**Metrics**:
- Request latency (p50, p95, p99)
- Error rates by endpoint
- AI agent response times
- Database query performance

**Alerts**:
- Error rate > 5% for 5 minutes
- API latency p95 > 2 seconds
- Database connection pool exhaustion
- Celery worker queue depth > 100

**Health Checks**:
- `/health`: Basic liveness check
- `/health/ready`: Readiness check (DB, Redis connectivity)

---

## Future Architecture Enhancements

**Scalability**:
- Horizontal scaling of backend services (already supports stateless)
- Read replicas for database (heavy read workload)
- CDN for static assets and frontend

**Features**:
- WebSocket support for real-time collaboration (future: coach/client)
- Push notifications via FCM/APNs
- Mobile apps (React Native, shared API)

**Observability**:
- Distributed tracing with OpenTelemetry
- APM integration (Datadog, New Relic)
- User session replay for debugging

**AI Enhancements**:
- Fine-tuned models for fitness domain
- RAG (Retrieval-Augmented Generation) for exercise library
- Multi-modal support (image recognition for meal logging)

---

## References

- **API Documentation**: `backend/docs/api-guide.md`
- **Deployment Guide**: `backend/docs/deployment.md`
- **External Integrations**: `backend/docs/external-integrations.md`
- **Feature Specification**: `specs/001-ai-fitness-planner/spec.md`
- **Data Model**: `specs/001-ai-fitness-planner/data-model.md`

---

**Last Updated**: November 17, 2025  
**Version**: 1.0  
**Maintained by**: Fitness Bot Development Team
