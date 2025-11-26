# Research & Technology Decisions: AI-Powered Fitness Planner

**Feature**: 001-ai-fitness-planner  
**Date**: 2025-11-15  
**Purpose**: Document technology choices, architectural decisions, and research findings for implementation

## Overview

This document captures the research and decision-making process for building an AI-powered fitness planning application. All technical context items have been evaluated and concrete choices made based on requirements, performance goals, and constitutional compliance.

---

## 1. Backend Framework: FastAPI

### Decision
Use **FastAPI 0.109+** as the backend web framework.

### Rationale
- **Performance**: Async/await support with uvicorn/hypercorn enables high concurrency (1000+ concurrent users requirement)
- **Type Safety**: Pydantic schemas provide automatic request validation and OpenAPI documentation generation
- **Developer Experience**: Automatic interactive API docs (Swagger UI), excellent error messages
- **Ecosystem**: Strong integration with SQLAlchemy, Redis, Celery, and testing frameworks
- **WebSocket Support**: Native WebSocket support for real-time AI streaming (FR-021)
- **Constitution Alignment**: Type annotations, automatic validation, built-in documentation generation

### Alternatives Considered
- **Flask**: Lacks built-in async support, requires more boilerplate for validation and documentation
- **Django + DRF**: Heavier framework, ORM tightly coupled, slower for API-only workloads
- **Node.js/Express**: Would require TypeScript on backend too, Python better for AI/ML ecosystem

---

## 2. AI Orchestration: OpenAI Agents SDK

### Decision
Use **OpenAI Agents SDK** (latest stable version) for conversational AI orchestration.

### Rationale
- **Function Calling**: Native support for tool definitions that can read/write database
- **Streaming**: Built-in streaming response support for conversational UX (< 1s to first token)
- **Context Management**: Automatic conversation history and context management
- **Flexibility**: Can define custom tools for fitness-specific operations
- **Reliability**: Production-ready SDK from OpenAI with good error handling

### Architecture
```python
# Agent Tools Pattern
@agent.tool
def get_current_plan(user_id: str) -> dict:
    """Retrieve user's active fitness plan"""
    # Database query via service layer
    
@agent.tool
def reschedule_workouts(user_id: str, reason: str, days_affected: int) -> dict:
    """Intelligently reschedule workouts due to disruption"""
    # Complex rescheduling logic
```

### Tool Organization
- **plan_tools.py**: create_plan, get_current_plan, update_plan, transition_phase
- **schedule_tools.py**: get_schedule, mark_complete, reschedule_for_disruption
- **workout_tools.py**: suggest_alternatives, modify_workout_intensity
- **meal_tools.py**: suggest_variations, update_meal_preferences
- **progress_tools.py**: get_adherence_stats, calculate_progress

### Alternatives Considered
- **LangChain**: More abstraction, but adds unnecessary complexity for our use case
- **Custom implementation**: Would require significant effort to replicate streaming, function calling, and conversation management
- **Direct OpenAI API**: Agents SDK provides better structure for tool management

---

## 3. Database: PostgreSQL with JSONB

### Decision
Use **PostgreSQL 15+** as primary database with **JSONB** columns for semi-structured data.

### Rationale
- **Relational + Flexible**: Strong relational model for core entities (users, plans, schedules) with JSONB for AI-generated content snapshots
- **JSONB Performance**: Indexable JSON storage for plan snapshots, conversation history
- **ACID Compliance**: Critical for user data integrity (zero data loss requirement)
- **Performance**: Supports 100K+ schedule entries with proper indexing (< 100ms query p95)
- **Scaling**: Read replicas, connection pooling, mature ecosystem
- **ORM Support**: Excellent SQLAlchemy/SQLModel integration

### JSONB Use Cases
```sql
-- Store AI-generated plan snapshot
fitness_plans.plan_snapshot JSONB
-- {
--   "phases": [...],
--   "workouts": [...],
--   "meals": [...],
--   "generated_at": "2025-11-15T10:30:00Z",
--   "model_version": "gpt-4-turbo"
-- }

-- Store conversation context
conversations.context JSONB
-- {
--   "user_preferences": {...},
--   "recent_topics": [...],
--   "pending_questions": [...]
-- }
```

### Schema Evolution Strategy
- **Alembic migrations**: Version-controlled schema changes
- **JSONB for flexibility**: AI-generated content can evolve without migrations
- **Multi-phase support**: Phase table with foreign keys to fitness_plans
  ```sql
  phases:
    id, fitness_plan_id, phase_number, name, objectives, 
    start_date, end_date, status
  ```

### Alternatives Considered
- **MongoDB**: Lacks strong relational guarantees, worse for schedule queries, no strong typing
- **MySQL**: Weaker JSONB support, less robust for complex queries
- **SQLite**: Not suitable for multi-user production workload

---

## 4. Caching & Background Jobs: Redis

### Decision
Use **Redis 7+** for caching and as message broker for background jobs.

### Rationale
- **Dual Purpose**: Single technology for both caching and job queue (simpler ops)
- **Performance**: Sub-millisecond cache reads (critical for < 500ms API p95)
- **Persistence**: Optional persistence for job queue durability
- **Pub/Sub**: Can support future real-time features (notifications, multi-device sync)
- **Celery/RQ Support**: Both background job libraries integrate seamlessly

### Caching Strategy
```python
# High-frequency reads
cache_keys = {
    f"user:{user_id}:current_plan",     # TTL: 1 hour
    f"user:{user_id}:schedule:{date}",  # TTL: 24 hours
    f"user:{user_id}:progress:summary", # TTL: 1 hour
}

# Invalidation on writes
# - Plan updates → invalidate current_plan
# - Schedule completion → invalidate schedule cache
# - Progress updates → invalidate progress summary
```

### Background Jobs
- **Long-running plan generation**: 10-30s AI generation doesn't block API
- **Periodic schedule recalculations**: Check for missed workouts, suggest rest days
- **Future: Notifications**: Workout reminders, milestone celebrations

### Alternatives Considered
- **Memcached**: Cache-only, no job queue support
- **RabbitMQ**: Separate from cache, more operational complexity
- **No caching**: Would struggle to meet < 500ms API response requirement

---

## 5. ORM & Migrations: SQLAlchemy + Alembic

### Decision
Use **SQLAlchemy 2.x** (or **SQLModel**) with **Alembic** for migrations.

### Rationale
- **Type Safety**: SQLModel combines Pydantic with SQLAlchemy for end-to-end types
- **Async Support**: SQLAlchemy 2.x has first-class async support (FastAPI compatibility)
- **Query Builder**: Powerful query API, prevents SQL injection
- **Migration Management**: Alembic provides version-controlled, reviewable migrations
- **Constitution Compliance**: Type annotations, explicit queries, no string-based SQL

### Model Example
```python
# SQLModel approach (Pydantic + SQLAlchemy hybrid)
class FitnessPlan(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    goal_description: str
    duration_weeks: int
    start_date: date
    target_end_date: date
    current_status: str  # active, completed, paused
    plan_snapshot: dict = Field(sa_column=Column(JSONB))  # AI-generated plan
    
    # Relationships
    phases: List["Phase"] = Relationship(back_populates="fitness_plan")
```

### Alternatives Considered
- **Raw SQL**: Error-prone, lacks type safety, harder to maintain
- **Django ORM**: Requires Django framework, less flexible
- **Tortoise ORM**: Less mature ecosystem, fewer resources

---

## 6. Background Workers: Celery

### Decision
Use **Celery** with **Redis** as message broker for background job processing.

### Rationale
- **Mature**: Production-proven, extensive documentation
- **Retries**: Built-in retry logic with exponential backoff
- **Monitoring**: Flower UI for monitoring job status
- **Async Tasks**: Can run long-running AI generation without blocking API
- **Scheduled Tasks**: Beat scheduler for periodic tasks (schedule recalculation)

### Task Architecture
```python
@celery_app.task(bind=True, max_retries=3)
def generate_fitness_plan(self, user_id: str, goal_data: dict):
    """Long-running AI plan generation (10-30s)"""
    try:
        # Call OpenAI Agents SDK
        # Generate comprehensive plan
        # Store in database
        return {"status": "complete", "plan_id": plan_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Alternatives Considered
- **RQ**: Simpler than Celery, but less feature-rich (no retries, less monitoring)
- **Dramatiq**: Good alternative, but smaller ecosystem
- **No background workers**: Would block API during 30s plan generation (violates < 2s requirement)

---

## 7. Frontend Framework: Next.js 14 with App Router

### Decision
Use **Next.js 14+** with **App Router**, **TypeScript**, and **React 18**.

### Rationale
- **Performance**: Server components, streaming, image optimization (meets FCP < 1.5s, TTI < 3.5s)
- **SEO**: Server-side rendering for landing pages (important for growth)
- **Developer Experience**: File-based routing, hot reload, TypeScript support
- **Full-Stack**: API routes for auth callbacks, can proxy to backend
- **Deployment**: Vercel, Netlify, or containerized deployment options
- **Ecosystem**: Huge React ecosystem, shadcn/ui integration

### App Router Architecture
```typescript
app/
├── layout.tsx                 // Root layout with providers
├── page.tsx                   // Landing page (SSR)
├── (auth)/                    // Auth route group (separate layout)
│   ├── login/page.tsx
│   └── signup/page.tsx
└── dashboard/                 // Protected routes
    ├── layout.tsx             // Dashboard layout with nav
    ├── page.tsx               // Overview
    ├── plan/page.tsx          // Plan view
    ├── schedule/page.tsx      // Calendar
    ├── progress/page.tsx      // Charts
    └── chat/page.tsx          // AI agent
```

### Alternatives Considered
- **Create React App**: Deprecated, no SSR, slower builds
- **Vite + React**: Great DX but requires custom SSR setup, no file-based routing
- **Remix**: Strong alternative, but smaller ecosystem than Next.js
- **SvelteKit**: Different paradigm, smaller hiring pool

---

## 8. Authentication: NextAuth.js

### Decision
Use **NextAuth.js (Auth.js)** for authentication with JWT strategy.

### Rationale
- **Next.js Integration**: First-class Next.js support, API routes, middleware
- **Multiple Providers**: Email/password, OAuth (Google, Apple) for future expansion
- **Session Management**: Secure JWT tokens with refresh mechanism
- **Backend Trust**: FastAPI validates JWT signature, trusts NextAuth tokens
- **Constitution Compliance**: Explicit security, no credentials in localStorage

### Auth Flow
```
1. User logs in via NextAuth (frontend)
2. NextAuth issues JWT with user_id, expiry
3. Frontend includes JWT in Authorization header
4. FastAPI middleware validates JWT signature
5. FastAPI extracts user_id from claims
6. Database queries filtered by authenticated user_id
```

### Security
- **JWT Signing**: HS256 or RS256, shared secret or public key verification
- **HTTPS Only**: Cookies with secure flag in production
- **CSRF Protection**: Built into NextAuth
- **Refresh Tokens**: Automatic token refresh before expiry

### Alternatives Considered
- **Clerk**: SaaS solution, but adds external dependency and cost
- **Auth0**: Similar to Clerk, overkill for MVP
- **Custom Auth**: Reinventing the wheel, higher security risk

---

## 9. UI Components: shadcn/ui

### Decision
Use **shadcn/ui** component library built on **Radix UI** and **Tailwind CSS**.

### Rationale
- **Accessibility**: Radix UI primitives are WCAG 2.1 Level AA compliant (constitutional requirement)
- **Customizable**: Components copied into project, full control over styling
- **Tailwind**: Utility-first CSS, consistent design tokens
- **TypeScript**: Full type safety for component props
- **No Runtime**: Components compile away, no runtime library (performance benefit)
- **Constitution Compliance**: Visual consistency, accessibility built-in

### Component Strategy
```bash
# Install and configure shadcn/ui
npx shadcn-ui@latest init

# Add components as needed
npx shadcn-ui@latest add button card dialog input textarea

# Components live in src/components/ui/
# Customize as needed for fitness domain
```

### Alternatives Considered
- **Material-UI**: Heavy runtime, harder to customize, not as accessible out-of-box
- **Chakra UI**: Good accessibility, but heavier runtime, different styling approach
- **Ant Design**: Enterprise-focused, too opinionated for consumer app
- **Headless UI**: Good, but shadcn/ui is better integrated with Tailwind

---

## 10. Real-Time Communication: Server-Sent Events (SSE)

### Decision
Use **Server-Sent Events (SSE)** for streaming AI responses to frontend.

### Rationale
- **Simplicity**: HTTP-based, no WebSocket handshake complexity
- **Browser Support**: Wide browser support, fallback to polling
- **FastAPI Support**: Built-in SSE support with StreamingResponse
- **Unidirectional**: Perfect for AI streaming (server → client)
- **Automatic Reconnection**: Browser handles reconnection automatically

### Implementation
```python
# Backend: FastAPI SSE endpoint
@router.get("/ai/stream")
async def stream_ai_response(
    message: str,
    user_id: UUID = Depends(get_current_user)
):
    async def event_generator():
        async for chunk in agent.stream_response(user_id, message):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Frontend: EventSource API
const eventSource = new EventSource(`/api/ai/stream?message=${msg}`);
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    appendToChat(data.chunk);
};
```

### Alternatives Considered
- **WebSockets**: Bidirectional overkill for one-way streaming, more complex connection management
- **Long Polling**: Less efficient, higher latency
- **gRPC Streaming**: Requires binary protocol support in browser, more complex

---

## 11. Testing Strategy

### Backend Testing (pytest)

**Unit Tests**: Services, utilities, date calculations
```python
# tests/unit/services/test_schedule_service.py
def test_reschedule_for_missed_workouts(db_session):
    # Given: User missed 2 workouts
    # When: Reschedule service called
    # Then: Workouts moved to future dates, timeline extended
    pass
```

**Integration Tests**: API endpoints, database interactions
```python
# tests/integration/test_plan_workflow.py
async def test_create_and_retrieve_plan(async_client, auth_headers):
    # Create plan via API
    response = await async_client.post("/api/v1/fitness-plans", json=plan_data, headers=auth_headers)
    assert response.status_code == 201
    # Retrieve plan
    plan_id = response.json()["id"]
    response = await async_client.get(f"/api/v1/fitness-plans/{plan_id}", headers=auth_headers)
    assert response.status_code == 200
```

**Contract Tests**: OpenAPI schema validation
```python
# tests/contract/test_plans_api.py
def test_create_plan_matches_openapi_schema(client):
    # Validate request/response against OpenAPI spec
    pass
```

### Frontend Testing (Vitest + Playwright)

**Component Tests**: UI components in isolation
```typescript
// tests/components/workout-card.test.tsx
import { render, screen } from '@testing-library/react';
import { WorkoutCard } from '@/components/fitness/workout-card';

test('displays workout name and exercises', () => {
    render(<WorkoutCard workout={mockWorkout} />);
    expect(screen.getByText('Upper Body Strength')).toBeInTheDocument();
    expect(screen.getByText('5 exercises')).toBeInTheDocument();
});
```

**E2E Tests**: Critical user journeys
```typescript
// tests/e2e/plan-creation.spec.ts
test('user can create fitness plan through AI conversation', async ({ page }) => {
    await page.goto('/dashboard/chat');
    await page.fill('[data-testid="chat-input"]', 'I want to lose 15 pounds in 3 months');
    await page.click('[data-testid="send-button"]');
    // Assert AI responds with questions
    // Fill out conversation
    // Assert plan created
    await expect(page.locator('[data-testid="plan-overview"]')).toBeVisible();
});
```

### Coverage Targets
- **Backend**: 80% overall, 100% for critical paths (schedule calculation, rescheduling logic, AI tools)
- **Frontend**: 70% overall, 100% for business logic hooks

---

## 12. DevOps & Deployment

### Docker Compose Setup

```yaml
# docker-compose.yml (local development)
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fitness_bot
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/fitness_bot
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

  worker:
    build: ./backend
    command: celery -A src.workers.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/fitness_bot
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXTAUTH_SECRET: dev_secret_change_in_prod
      NEXTAUTH_URL: http://localhost:3000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Environment Configuration

**Backend (.env)**:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/fitness_bot
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://host:6379/0

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Security
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://app.fitnessbot.com
```

**Frontend (.env.local)**:
```bash
# API
NEXT_PUBLIC_API_URL=https://api.fitnessbot.com

# Auth
NEXTAUTH_SECRET=...
NEXTAUTH_URL=https://app.fitnessbot.com
JWT_SECRET=...  # Same as backend for token validation

# Analytics (future)
NEXT_PUBLIC_ANALYTICS_ID=...
```

### Deployment Strategy

**Option 1: Cloud-Native Containers (Recommended)**
- **Backend + Worker**: Deploy to AWS ECS, GCP Cloud Run, or Azure Container Apps
- **Frontend**: Deploy to Vercel (optimal Next.js support) or containerized
- **Database**: Managed PostgreSQL (AWS RDS, GCP Cloud SQL, Azure Database)
- **Redis**: Managed Redis (AWS ElastiCache, GCP Memorystore, Azure Cache)
- **Secrets**: AWS Secrets Manager, GCP Secret Manager, Azure Key Vault

**Option 2: Kubernetes**
- Full control, more operational complexity
- Use Helm charts for deployment
- HPA for auto-scaling

**Option 3: Single VPS (Not Recommended for Production)**
- Docker Compose on single server
- Suitable only for MVP testing with <100 users

### CI/CD Pipeline

```yaml
# .github/workflows/backend-tests.yml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt
      - name: Run linting
        run: |
          cd backend
          ruff check src/
          black --check src/
      - name: Run tests
        run: |
          cd backend
          pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 13. Linting & Formatting

### Backend (Python)

**Ruff**: Fast Python linter (replaces flake8, isort, others)
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]  # Error, pyflakes, isort, naming, warnings, pyupgrade

[tool.ruff.isort]
known-first-party = ["src"]
```

**Black**: Code formatter
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**mypy**: Type checking
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Frontend (TypeScript)

**ESLint**: Linter
```json
// .eslintrc.json
{
  "extends": ["next/core-web-vitals", "prettier"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn"
  }
}
```

**Prettier**: Code formatter
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

**TypeScript**: Strict mode
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true
  }
}
```

---

## 14. Performance Optimization Strategies

### Database Optimization
```sql
-- Indexes for common queries
CREATE INDEX idx_fitness_plans_user_id ON fitness_plans(user_id);
CREATE INDEX idx_schedule_entries_user_date ON schedule_entries(user_id, date);
CREATE INDEX idx_workouts_plan_id ON workouts(workout_plan_id);
CREATE INDEX idx_meals_plan_id ON meals(meal_plan_id);

-- JSONB indexes for queries on plan snapshots
CREATE INDEX idx_plan_snapshot_phases ON fitness_plans USING GIN ((plan_snapshot->'phases'));

-- Composite index for schedule queries
CREATE INDEX idx_schedule_user_date_status ON schedule_entries(user_id, date, completion_status);
```

### Caching Strategy
```python
# Redis cache patterns
async def get_current_plan(user_id: UUID) -> FitnessPlan:
    cache_key = f"user:{user_id}:current_plan"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return FitnessPlan.parse_raw(cached)
    
    # Query database
    plan = await db.query(FitnessPlan).filter(...).first()
    
    # Set cache (1 hour TTL)
    await redis.setex(cache_key, 3600, plan.json())
    return plan
```

### API Pagination
```python
# Limit response sizes (constitutional requirement: max 100 items)
@router.get("/workouts", response_model=Page[WorkoutSchema])
async def list_workouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    offset = (page - 1) * page_size
    workouts = await db.query(Workout).offset(offset).limit(page_size).all()
    total = await db.query(Workout).count()
    return Page(items=workouts, total=total, page=page, page_size=page_size)
```

### Frontend Optimization
```typescript
// Next.js image optimization
import Image from 'next/image';
<Image src="/workout.jpg" alt="..." width={400} height={300} />

// Lazy loading components
const ProgressChart = dynamic(() => import('@/components/fitness/progress-chart'), {
    loading: () => <Skeleton />,
    ssr: false  // Client-side only (chart library)
});

// React query for data fetching with cache
const { data: plan } = useQuery(['plan', userId], fetchPlan, {
    staleTime: 5 * 60 * 1000,  // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
});
```

---

## Summary of Key Decisions

| Area | Technology | Primary Reason |
|------|-----------|----------------|
| Backend Framework | FastAPI | Async, type safety, performance |
| AI Orchestration | OpenAI Agents SDK | Function calling, streaming, managed context |
| Database | PostgreSQL 15+ | ACID, JSONB, relational integrity |
| Caching/Queue | Redis 7+ | Performance, dual-purpose (cache + jobs) |
| ORM | SQLAlchemy 2.x / SQLModel | Type safety, async support, migrations |
| Background Jobs | Celery | Mature, retries, monitoring |
| Frontend | Next.js 14 App Router | Performance (SSR, streaming), DX |
| Auth | NextAuth.js | Next.js integration, security |
| UI Components | shadcn/ui + Radix | Accessibility, customizable, no runtime |
| Streaming | Server-Sent Events | Simplicity, browser support, unidirectional |
| Testing (Backend) | pytest | Python standard, great async support |
| Testing (Frontend) | Vitest + Playwright | Fast unit tests, reliable E2E |
| Linting (Backend) | Ruff + Black | Fast, comprehensive, auto-formatting |
| Linting (Frontend) | ESLint + Prettier | TypeScript support, consistent formatting |
| Deployment | Docker + Cloud Containers | Portability, scaling, managed services |

---

## 14. AI Testing Strategy: MLflow + Manual Testing

### Decision
Use **MLflow** for comprehensive AI agent testing and evaluation, with manual testing during active development.

### Rationale
- **MLflow Integration**: Purpose-built for LLM/agent evaluation with prompt tracking, response logging, and metrics
- **Deferred Testing**: AI agent unit tests are deferred until MLflow setup phase to avoid test duplication
- **Manual Validation**: During development, AI agents and tools are manually tested through conversation UI
- **Production Metrics**: MLflow enables proper evaluation of conversation quality, tool usage, and plan generation accuracy
- **Cost Efficiency**: Avoid writing throwaway unit tests that don't reflect real-world agent behavior

### Testing Approach
```text
Development Phase (Current):
- Manual testing via conversation UI
- Verify tool registration and availability
- Test basic agent routing and responses
- Validate database integration

MLflow Phase (Later):
- Systematic prompt evaluation
- Tool usage pattern analysis
- Conversation flow testing
- A/B testing different instructions
- Response quality metrics
- Cost and latency tracking
```

### Scope
- **Manual Testing**: All AI agent tools and conversations during development
- **Integration Tests**: Database operations, API endpoints, schedule logic
- **MLflow Tests**: Agent behavior, prompt effectiveness, conversation quality, tool selection accuracy

### Constitution Alignment
- Pragmatic testing approach that focuses resources where they provide most value
- Avoid premature optimization of test infrastructure
- Use production-grade tools (MLflow) for AI evaluation rather than basic unit tests
- Manual testing during development ensures rapid iteration

---

## Open Questions & Future Considerations

### Resolved for MVP
All technical context questions have been resolved with concrete choices above.

### Future Enhancements (Post-MVP)
- **Mobile Apps**: React Native or native iOS/Android apps
- **Offline Support**: PWA with service workers, local-first architecture
- **Wearable Integration**: Apple Health, Google Fit, Garmin, Whoop
- **Social Features**: Share plans, community challenges, trainer marketplace
- **Advanced Analytics**: Machine learning for better plan recommendations
- **Video Content**: Exercise demonstration videos, meal prep tutorials
- **Internationalization**: Multi-language support, region-specific meal recommendations

### Monitoring & Observability (Implementation Phase)
- **Application Metrics**: Prometheus + Grafana or DataDog
- **Error Tracking**: Sentry for backend and frontend errors
- **Logging**: Structured logging (JSON), centralized via CloudWatch/Stackdriver
- **APM**: Application performance monitoring for API latency tracking

---

## Constitutional Alignment Summary

✅ **Code Quality**: Type safety (Python type hints, TypeScript strict mode), linting (Ruff, ESLint), documentation (OpenAPI, TSDoc)

✅ **Test-First**: pytest for backend TDD, Vitest for frontend, contract tests, 80%+ coverage target

✅ **UX Consistency**: shadcn/ui for visual consistency, WCAG 2.1 AA via Radix, < 2s response times via caching

✅ **Performance**: Architecture supports all constitutional requirements (< 500ms API p95, < 100ms DB queries, 1000 concurrent users, horizontal scaling)

All technology choices support constitutional principles and enable high-quality, maintainable code.
