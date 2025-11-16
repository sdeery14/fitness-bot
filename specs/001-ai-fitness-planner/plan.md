# Implementation Plan: AI-Powered Fitness Planner

**Branch**: `001-ai-fitness-planner` | **Date**: 2025-11-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-fitness-planner/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a web application that enables users to create, follow, and continuously update personalized fitness plans through conversational AI interaction. The system uses a multi-agent orchestration architecture where specialist agents (Conversation Agent, Fitness Plan Agent, Workout Plan Agent, Meal Plan Agent) run in parallel to generate comprehensive plans combining workout routines and meal plans. The AI maintains daily schedules, intelligently adapts to disruptions, and provides continuous improvement suggestions. State management via Redis/PostgreSQL with storage references enables efficient context handling, while async generation with streaming progress updates and background notifications ensures responsive UX within 30-second plan generation targets.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend), Node.js 20.x (frontend runtime)

**Primary Dependencies**: 
- Backend: FastAPI 0.109+, OpenAI Agents SDK (latest), SQLAlchemy/SQLModel 2.x, Alembic, Redis 7+, Celery
- Frontend: Next.js 14+ (App Router), NextAuth.js, shadcn/ui + Radix UI, React 18+

**Storage**: 
- PostgreSQL 15+ (primary application database with JSONB support for AI-generated plan snapshots)
- Redis 7+ (ephemeral state storage for conversation context, caching, background job queue)

**Testing**: 
- Backend: pytest 8.x, pytest-asyncio, httpx (API testing), pytest-cov (coverage: 80% minimum, 100% critical paths)
- Frontend: Vitest, React Testing Library, Playwright (E2E)
- Linting: Ruff/Black (Python), ESLint/Prettier (TypeScript)

**Target Platform**: Linux containers (Docker), deployable to cloud platforms (AWS ECS, GCP Cloud Run, Azure Container Apps) with managed PostgreSQL and Redis services

**Project Type**: Web application (backend API + frontend web app)

**Performance Goals**: 
- API endpoints: p95 < 500ms, p99 < 1000ms
- AI responses: streaming starts < 1s, complete generation < 30s (90% of cases)
- Page loads: FCP < 1.5s, TTI < 3.5s
- Database queries: p95 < 100ms
- Support 1000 concurrent users

**Constraints**: 
- API response times: standard operations < 2s (constitutional requirement)
- Real-time AI streaming required for conversational UX
- Multi-device support with data synchronization < 5s
- WCAG 2.1 Level AA accessibility compliance
- Zero data loss for user plans and progress

**Scale/Scope**: 
- Initial: 1000 active users, 10K+ fitness plans, 100K+ schedule entries
- Growth: Horizontal scaling support for 10K+ concurrent users
- Codebase: ~15-20K LOC backend, ~10-15K LOC frontend
- ~25 API endpoints, 14 core entities (from data-model.md), 5 user stories (P1-P5)
- Multi-agent AI architecture: 4 specialist agents with parallel execution

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Quality Standards ✅

- **Readability**: Python with type hints, TypeScript with strict mode, clear naming conventions
- **Modularity**: Service-oriented architecture (models → schemas → services → API endpoints → AI tools), single responsibility per module/class
- **Type Safety**: TypeScript strict mode enforced, Python type annotations with mypy validation
- **Error Handling**: FastAPI exception handlers, frontend error boundaries, explicit error types in API contracts
- **Documentation**: OpenAPI/Swagger docs auto-generated, TSDoc comments, docstrings for all public APIs
- **Code Review**: Required via git workflow
- **Linting**: Ruff/Black (Python), ESLint/Prettier (TypeScript) - zero warnings enforced in CI/CD

### II. Test-First Development (NON-NEGOTIABLE) ✅

- **TDD Approach**: Tests written before implementation for all user stories (P1-P5)
- **Coverage Goals**: 80% minimum maintained, 100% for critical paths:
  - AI agent tools (workout selection, meal generation, schedule rescheduling)
  - Schedule calculation logic
  - Plan generation orchestration
- **Test Types**:
  - Unit tests: pytest for backend services, Vitest for frontend utilities
  - Integration tests: API endpoint tests (httpx), database interaction tests
  - Contract tests: OpenAPI contract validation, AI tool interface tests
  - E2E tests: Playwright for critical user flows (plan creation, schedule tracking)
- **Test Independence**: pytest fixtures enable isolated tests, database rollback per test, frontend components tested in isolation
- **CI/CD**: All tests must pass before merge to main branch

### III. User Experience Consistency ✅

- **Response Time**: 
  - API < 500ms p95 (exceeds constitutional < 2s requirement for standard ops)
  - Visual feedback < 200ms (loading states, optimistic UI updates)
  - AI streaming < 1s to first token (SSE for real-time responses)
- **Error Messages**: User-friendly messages in API contracts (error.code + error.message), no stack traces exposed to clients
- **Visual Consistency**: shadcn/ui component library provides consistent design tokens (colors, spacing, typography)
- **Accessibility**: WCAG 2.1 Level AA compliance via Radix UI primitives (keyboard navigation, ARIA labels, screen reader support)
- **Progressive Disclosure**: Chat interface reveals complexity gradually, dashboard shows today's schedule first, plan details on demand
- **Confirmation**: Required for destructive actions (plan deletion, goal changes) via dialog components
- **State Persistence**: PostgreSQL for permanent data, Redis for session state, JWT tokens for stateless auth
- **Mobile Responsiveness**: Next.js responsive design, mobile-first approach, touch-friendly UI

### IV. Performance Requirements ✅

- **Response Times**: 
  - API endpoints: p95 < 500ms, p99 < 1000ms ✅ (meets requirement)
  - Database queries: p95 < 100ms ✅ (meets requirement)
  - Page loads: FCP < 1.5s, TTI < 3.5s ✅ (meets requirement)
- **Throughput**: 1000 concurrent users ✅ (meets requirement)
- **Resource Efficiency**: 
  - Backend baseline: ~150MB per instance
  - Per-user overhead: ~3-5MB ✅ (within < 5MB requirement)
  - Redis caching reduces DB load, async workers prevent blocking
- **Scalability**: Stateless API design enables horizontal scaling via container orchestration (Docker Swarm/Kubernetes)
- **Optimization**:
  - Database indexes on all foreign keys and high-cardinality columns (user_id, schedule_date, plan_id)
  - Pagination enforced: max 100 items per response ✅
  - CDN for static assets via Next.js automatic optimization
  - Redis caching: current plan (5 min TTL), upcoming schedule (1 min TTL)
- **Monitoring**: Application metrics tracked (plan generation time, API latency, DB query performance)

### Quality Gates Readiness

1. ✅ **Constitution Compliance**: All 4 principles addressed and validated above
2. ✅ **Code Quality**: Linting configured (Ruff, ESLint), type safety enforced (Python types, TypeScript strict)
3. ✅ **Test Coverage**: TDD approach planned, 80%+ coverage target, 100% for critical AI/schedule logic
4. ✅ **Performance**: Architecture supports required thresholds (< 500ms API p95, 1000 concurrent users, horizontal scaling)
5. ✅ **Accessibility**: Frontend framework (shadcn/ui + Radix UI) provides WCAG 2.1 AA compliance out-of-box
6. ✅ **Documentation**: OpenAPI auto-generated for backend, TSDoc for frontend, comprehensive quickstart.md created
7. ✅ **Security**: JWT auth with bcrypt/Argon2 password hashing, input validation via Pydantic, SQL injection prevention via ORM

**Status**: ✅ PASSED - No constitutional violations

### Post-Phase 1 Design Verification

*Re-evaluated after completing data-model.md and api-contracts.md*

#### Code Quality Standards ✅
- **Data Model**: 14 entities with clear single responsibilities, full SQL schema with proper indexes
- **Type Safety**: All database columns have explicit types, JSONB for semi-structured AI content
- **Documentation**: Comprehensive docstrings in data-model.md, API contracts with request/response schemas
- **Modularity**: Clean separation (models → schemas → services → API endpoints → AI tools)
- **Error Handling**: API contracts define error codes for all endpoints (400, 401, 404, 422, 500)

#### Test-First Development ✅
- **Test Structure**: Defined in project structure (unit/integration/contract test directories)
- **Coverage**: quickstart.md documents test execution (`pytest --cov`, `npm test`)
- **Critical Paths**: 100% coverage planned for AI tools, schedule calculations, plan generation
- **Independence**: pytest fixtures for isolated tests, database rollback per test

#### User Experience Consistency ✅
- **Response Time**: API contracts show pagination (max 100 items ✅), Redis caching strategy defined
- **Error Messages**: Structured error responses in API contracts with `error.code` and `error.message`
- **Accessibility**: shadcn/ui components (WCAG 2.1 Level AA compliant) in tech stack
- **State Persistence**: PostgreSQL for permanent data, `plan_snapshot` JSONB preserves full AI-generated plans
- **Progressive Disclosure**: Chat interface with streaming responses (SSE), dashboard with today's schedule first

#### Performance Requirements ✅
- **Database Indexes**: All entities have indexes on foreign keys and query patterns (user_id, entry_date, current_status)
- **Pagination**: API contracts enforce max 100 items per page ✅
- **Caching**: Redis for current plan, upcoming schedule (quickstart documents strategy)
- **Query Optimization**: JSONB GIN indexes for AI-generated content, composite indexes for common queries
- **Scalability**: Stateless API design (JWT auth), background workers (Celery) for long-running tasks

**Post-Phase 1 Status**: ✅ PASSED - Design maintains full constitutional compliance

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-fitness-planner/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (technology decisions documented)
├── data-model.md        # Phase 1 output (14 entities with SQL schema)
├── quickstart.md        # Phase 1 output (developer onboarding guide)
├── contracts/           # Phase 1 output (API endpoint contracts)
│   └── api-contracts.md # REST API with 25+ endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Environment configuration, settings
│   ├── database.py                  # Database connection, session management
│   ├── models/                      # SQLAlchemy/SQLModel ORM models
│   │   ├── __init__.py
│   │   ├── user.py                  # User, auth credentials
│   │   ├── fitness_plan.py          # FitnessPlan, Phase
│   │   ├── workout.py               # WorkoutPlan, Workout, Exercise
│   │   ├── meal.py                  # MealPlan, Meal
│   │   ├── schedule.py              # Schedule, ScheduleEntry
│   │   ├── progress.py              # ProgressRecord, Milestone
│   │   └── conversation.py          # Conversation, Message, DisruptionEvent
│   ├── schemas/                     # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── fitness_plan.py
│   │   ├── workout.py
│   │   ├── meal.py
│   │   ├── schedule.py
│   │   ├── progress.py
│   │   └── conversation.py
│   ├── api/                         # FastAPI routers/endpoints
│   │   ├── __init__.py
│   │   ├── deps.py                  # Dependency injection (auth, DB session)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Authentication endpoints (register, login, refresh)
│   │   │   ├── users.py             # User profile management
│   │   │   ├── fitness_plans.py     # Plan CRUD operations
│   │   │   ├── workouts.py          # Workout management
│   │   │   ├── meals.py             # Meal management
│   │   │   ├── schedules.py         # Schedule queries, completion tracking
│   │   │   ├── progress.py          # Progress tracking, statistics
│   │   │   └── ai_agent.py          # AI conversation endpoints (chat, SSE streaming)
│   ├── services/                    # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Authentication, token management
│   │   ├── user_service.py          # User operations
│   │   ├── plan_service.py          # Plan generation, modification logic
│   │   ├── schedule_service.py      # Schedule calculations, rescheduling
│   │   ├── progress_service.py      # Progress calculations, adherence stats
│   │   └── ai_orchestration.py      # Multi-agent orchestration (Conversation → Fitness → [Workout || Meal])
│   ├── ai/                          # AI agent tools and orchestration
│   │   ├── __init__.py
│   │   ├── agent.py                 # Main agent initialization
│   │   ├── app_agents/              # Application-specific agents (avoid "agents" alone - conflicts with OpenAI SDK)
│   │   │   ├── __init__.py
│   │   │   ├── conversation_agent.py    # User interaction agent
│   │   │   ├── fitness_plan_agent.py    # Plan coordination agent
│   │   │   ├── workout_plan_agent.py    # Exercise selection agent
│   │   │   └── meal_plan_agent.py       # Nutrition planning agent
│   │   ├── tools/                   # Agent tools (functions AI can call)
│   │   │   ├── __init__.py
│   │   │   ├── plan_tools.py        # get_current_plan, create_plan, update_plan
│   │   │   ├── schedule_tools.py    # get_schedule, mark_complete, reschedule
│   │   │   ├── workout_tools.py     # suggest_alternatives, modify_workout
│   │   │   ├── meal_tools.py        # suggest_meal_variations, update_meals
│   │   │   └── progress_tools.py    # get_progress, calculate_adherence
│   │   └── prompts/                 # System prompts for agents
│   │       ├── system_prompt.txt
│   │       └── tool_descriptions.py
│   ├── workers/                     # Background job definitions
│   │   ├── __init__.py
│   │   ├── celery_app.py            # Celery initialization
│   │   ├── plan_generation.py       # Async plan generation (multi-agent orchestration)
│   │   ├── schedule_recalc.py       # Periodic schedule recalculations
│   │   └── notifications.py         # Plan complete notifications
│   ├── integrations/                # External service integrations
│   │   ├── __init__.py
│   │   ├── usda_fooddata.py         # USDA FoodData Central API client
│   │   └── exercise_database.py     # Curated exercise database queries
│   ├── utils/                       # Utility functions
│   │   ├── __init__.py
│   │   ├── cache.py                 # Redis caching utilities
│   │   ├── validators.py            # Input validation helpers
│   │   └── date_utils.py            # Date/time manipulation
│   └── middleware/                  # FastAPI middleware
│       ├── __init__.py
│       ├── auth_middleware.py       # JWT validation
│       └── logging_middleware.py    # Request logging
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixtures, test DB setup
│   ├── contract/                    # API contract tests
│   │   ├── test_auth_api.py
│   │   ├── test_plans_api.py
│   │   ├── test_schedule_api.py
│   │   └── test_ai_agent_api.py
│   ├── integration/                 # Integration tests
│   │   ├── test_plan_workflow.py    # End-to-end plan creation
│   │   ├── test_schedule_workflow.py
│   │   ├── test_ai_tools.py         # AI tool integration with DB
│   │   ├── test_rescheduling.py
│   │   └── test_multi_agent.py      # Parallel agent execution
│   └── unit/                        # Unit tests
│       ├── services/
│       │   ├── test_plan_service.py
│       │   ├── test_schedule_service.py
│       │   └── test_progress_service.py
│       ├── ai/
│       │   ├── test_orchestration.py
│       │   └── test_agent_tools.py
│       └── utils/
│           ├── test_validators.py
│           └── test_date_utils.py
├── alembic/                         # Database migrations
│   ├── versions/
│   └── env.py
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml                   # Python project config, Ruff/Black settings
├── Dockerfile
└── .env.example

frontend/
├── src/
│   ├── app/                         # Next.js App Router
│   │   ├── layout.tsx               # Root layout
│   │   ├── page.tsx                 # Home/landing page
│   │   ├── (auth)/                  # Auth route group
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   ├── dashboard/               # Main dashboard
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx             # Overview
│   │   │   ├── plan/                # Fitness plan view
│   │   │   │   └── page.tsx
│   │   │   ├── schedule/            # Calendar/schedule view
│   │   │   │   └── page.tsx
│   │   │   ├── progress/            # Progress tracking
│   │   │   │   └── page.tsx
│   │   │   └── chat/                # AI agent chat
│   │   │       └── page.tsx
│   │   └── api/                     # Next.js API routes (auth callbacks)
│   │       └── auth/
│   │           └── [...nextauth]/
│   │               └── route.ts
│   ├── components/                  # React components
│   │   ├── ui/                      # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── textarea.tsx
│   │   │   └── ...
│   │   ├── layout/                  # Layout components
│   │   │   ├── navbar.tsx
│   │   │   ├── sidebar.tsx
│   │   │   └── footer.tsx
│   │   ├── chat/                    # Chat interface components
│   │   │   ├── chat-interface.tsx
│   │   │   ├── message-list.tsx
│   │   │   ├── message-input.tsx
│   │   │   └── streaming-response.tsx
│   │   ├── fitness/                 # Fitness-specific components
│   │   │   ├── plan-overview.tsx
│   │   │   ├── workout-card.tsx
│   │   │   ├── meal-card.tsx
│   │   │   ├── schedule-calendar.tsx
│   │   │   ├── daily-schedule.tsx
│   │   │   └── progress-chart.tsx
│   │   └── auth/                    # Auth components
│   │       ├── login-form.tsx
│   │       └── signup-form.tsx
│   ├── lib/                         # Utilities and helpers
│   │   ├── api-client.ts            # Typed API client for backend
│   │   ├── auth.ts                  # NextAuth configuration
│   │   ├── utils.ts                 # General utilities (cn, date formatting)
│   │   ├── websocket.ts             # SSE client for AI streaming
│   │   └── types.ts                 # Shared TypeScript types
│   ├── hooks/                       # React hooks
│   │   ├── use-api.ts               # API data fetching
│   │   ├── use-chat.ts              # Chat state management
│   │   ├── use-schedule.ts          # Schedule data management
│   │   └── use-progress.ts          # Progress tracking
│   ├── store/                       # Global state management (Zustand/Jotai)
│   │   ├── auth-store.ts
│   │   ├── plan-store.ts
│   │   └── schedule-store.ts
│   └── styles/
│       └── globals.css              # Global styles, Tailwind imports
├── tests/
│   ├── components/                  # Component tests (Vitest + React Testing Library)
│   │   ├── chat-interface.test.tsx
│   │   ├── workout-card.test.tsx
│   │   └── schedule-calendar.test.tsx
│   └── e2e/                         # End-to-end tests (Playwright)
│       ├── onboarding.spec.ts
│       ├── plan-creation.spec.ts
│       └── schedule-tracking.spec.ts
├── public/                          # Static assets
│   ├── images/
│   └── icons/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── components.json                  # shadcn/ui config
├── .eslintrc.json
├── .prettierrc
├── Dockerfile
└── .env.local.example

docker/                              # Docker orchestration
├── docker-compose.yml               # Local development setup
├── docker-compose.prod.yml          # Production-like setup
└── nginx.conf                       # Reverse proxy config (optional)

.github/                             # CI/CD workflows
├── copilot-instructions.md          # Updated via update-agent-context.ps1
└── workflows/
    ├── backend-tests.yml
    ├── frontend-tests.yml
    └── deploy.yml

docs/                                # Additional documentation
├── architecture.md
├── api-guide.md
└── deployment.md
```

**Structure Decision**: Web application architecture selected (Option 2 from template). Clean separation between `backend/` (Python/FastAPI) and `frontend/` (Next.js/TypeScript) enables independent development, testing, and deployment. Backend uses service-oriented architecture with clear layers: models (data), schemas (API contracts), services (business logic), api (HTTP endpoints), and ai (multi-agent orchestration with specialist agents). Frontend uses Next.js App Router with component-based architecture and centralized state management. Both projects are containerized with Docker for consistent development and deployment environments.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitutional violations identified. All complexity is justified by functional requirements:

- **Web application architecture**: Required for conversational UI (FR-021) and cross-device access (FR-042)
- **PostgreSQL + Redis**: Justified by data persistence requirements (FR-041) and performance goals (caching for < 500ms API response)
- **Background workers (Celery)**: Necessary for async plan generation without blocking UI (FR-067, FR-068, FR-069)
- **Multi-agent orchestration (4 specialist agents)**: Core requirement for efficient context management (FR-063) and parallel execution (FR-064, reducing plan generation time by 40% per SC-027)
- **OpenAI Agents SDK**: Core requirement for conversational AI fitness agent (FR-001, FR-021-FR-027)
- **JSONB columns in PostgreSQL**: Enables flexible storage of AI-generated plan snapshots (plan_snapshot, conversation_context) while maintaining relational integrity for structured queries

All architectural decisions align with constitutional principles and are necessary to meet functional requirements and success criteria.
