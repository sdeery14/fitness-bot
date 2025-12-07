# Quickstart Guide: AI-Powered Fitness Planner

**Feature**: 001-ai-fitness-planner  
**Date**: 2025-11-15  
**Audience**: Developers setting up local development environment

## Overview

This guide walks you through setting up a complete local development environment for the AI-powered fitness planning application.

**What You'll Get**:
- Backend API (`http://localhost:8000`) with FastAPI
- Frontend web app (`http://localhost:3000`) with Next.js
- PostgreSQL database, Redis cache, and background workers
- Full Docker Compose orchestration with hot-reload

**Estimated Setup Time**: 15-20 minutes

---

## Prerequisites

Ensure you have installed:

- **Docker Desktop 4.20+** (includes Docker Compose) - [Download](https://www.docker.com/products/docker-desktop)
- **Git 2.30+**
- **OpenAI API Key** - [Get one here](https://platform.openai.com/api-keys)
- **Code Editor** (VS Code recommended with Python, ESLint, Prettier, Docker extensions)

Verify installations:
```powershell
docker --version; docker-compose --version; git --version
```

---

## Step 1: Clone and Setup Repository

```powershell
git clone <repository-url>
cd fitness-bot
git checkout 001-ai-fitness-planner

# Verify structure - you should see: backend/, frontend/, docker/, specs/
ls
```

---

## Step 2: Configure Environment Variables

Set up a shorthand for docker-compose commands:
```powershell
$dc = "docker-compose -f docker/docker-compose.yml"
```

### Backend Environment

```powershell
cd backend
cp .env.example .env
# Edit backend/.env and set your OPENAI_API_KEY
```

**Key variables to configure in `backend/.env`**:
- `OPENAI_API_KEY=sk-your-key-here` (**REQUIRED**)
- `JWT_SECRET` (change from default for production)
- Other defaults should work for local development

See `backend/.env.example` for all available options.

### Frontend Environment

```powershell
cd ../frontend
cp .env.local.example .env.local
# Edit frontend/.env.local if needed (defaults work for local dev)
```

**Key variable in `frontend/.env.local`**:
- `JWT_SECRET` (must match backend value)

See `frontend/.env.local.example` for all options.

---

## Step 3: Start All Services

```powershell
# Return to project root
cd ..

# Start all services (first time takes 5-10 minutes to build)
docker-compose -f docker/docker-compose.yml up -d

# Verify all services are running
docker-compose -f docker/docker-compose.yml ps
```

All services should show "Up" status: postgres, redis, backend, worker, frontend.

---

## Step 4: Initialize Database

```powershell
# Run Alembic migrations
docker-compose -f docker/docker-compose.yml exec backend alembic upgrade head

# Verify tables created (should see 15+ tables)
# Uses credentials from backend/.env file
docker-compose -f docker/docker-compose.yml exec postgres psql -U fitness_user -d fitness_bot -c "\dt"
```

---

## Step 5: Verify Services

**Backend API**:
```powershell
curl http://localhost:8000/health
# Should return: {"status": "healthy", "version": "1.0.0"}
```

**API Documentation**: http://localhost:8000/docs (Swagger UI)

**Frontend**: http://localhost:3000 (landing page with hot-reload enabled)

---

## Step 6: Create Your First User

**Via Frontend**: 
1. Go to http://localhost:3000
2. Click "Sign Up" and complete the form

**Via API**:
```powershell
curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{\"email\":\"dev@example.com\",\"password\":\"DevPassword123!\",\"full_name\":\"Dev User\",\"current_fitness_level\":\"beginner\"}'
```

---

## Step 7: Test AI Agent

**Via Frontend**: Navigate to http://localhost:3000/dashboard/chat and type: "I want to lose 15 pounds in 3 months"

**Via API** (with PowerShell):
```powershell
# Login and get token
$response = curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{\"email\":\"dev@example.com\",\"password\":\"DevPassword123!\"}' | ConvertFrom-Json
$token = $response.data.access_token

# Start conversation
curl -X POST http://localhost:8000/api/v1/ai/conversations -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d '{\"conversation_type\":\"plan_creation\",\"initial_message\":\"I want to lose 15 pounds in 3 months\"}'
```

---

## Development Workflow

**Recommended: Full Docker Development**

All services run in Docker with hot-reload enabled:

- **Backend**: Edit files in `backend/src/`, FastAPI auto-reloads
- **Frontend**: Edit files in `frontend/src/`, Next.js Fast Refresh auto-updates browser
- **View logs**: Use `docker-compose -f docker/docker-compose.yml logs -f [service]`

**Alternative: Hybrid (Faster Frontend)**

For quicker frontend iteration, run frontend locally:

```powershell
# Start backend services only
docker-compose -f docker/docker-compose.yml up -d postgres redis backend celery_worker

# In frontend directory
cd frontend
npm install
npm run dev
```

Benefits: Faster hot-reload, better debugging, direct DevTools access.

**Database Schema Changes**:
1. Edit SQLAlchemy models in `backend/src/models/`
2. Generate migration: `docker-compose -f docker/docker-compose.yml exec backend alembic revision --autogenerate -m "Description"`
3. Apply: `docker-compose -f docker/docker-compose.yml exec backend alembic upgrade head`

---

## Running Tests

**Backend (pytest)**:
```powershell
# All tests
docker-compose -f docker/docker-compose.yml exec backend pytest

# With coverage
docker-compose -f docker/docker-compose.yml exec backend pytest --cov=src --cov-report=html

# Specific test
docker-compose -f docker/docker-compose.yml exec backend pytest tests/unit/services/test_schedule_service.py::test_reschedule_for_missed_workouts
```

**Frontend (Vitest)** - Component/Unit tests:
```powershell
# All unit tests (excludes E2E)
docker-compose -f docker/docker-compose.yml exec frontend npm test -- --run

# Watch mode (for active development)
docker-compose -f docker/docker-compose.yml exec frontend npm test

# Note: Currently no component tests exist (exits with "No test files found").
# Component tests will be added in future phases. E2E tests use Playwright (see below).
```

**E2E (Playwright)** - Full user flow tests (requires all services running):
```powershell
# From project root - run backend services first
docker-compose -f docker/docker-compose.yml up -d

# Run E2E tests
cd frontend
npm run test:e2e

# Options
npm run test:e2e -- --headed     # See browser
npm run test:e2e -- --debug      # Debug mode
npm run test:e2e -- --ui         # Interactive UI mode
```

---

## Linting and Formatting

**Backend**:
```powershell
docker-compose -f docker/docker-compose.yml exec backend ruff check src/ --fix
docker-compose -f docker/docker-compose.yml exec backend black src/
docker-compose -f docker/docker-compose.yml exec backend mypy src/
```

**Frontend**:
```powershell
docker-compose -f docker/docker-compose.yml exec frontend npm run lint -- --fix
docker-compose -f docker/docker-compose.yml exec frontend npm run format
docker-compose -f docker/docker-compose.yml exec frontend npm run type-check
```

---

## Common Management Tasks

**Database Access**:

*Option 1: Command Line (psql)*
```powershell
# PostgreSQL shell (credentials from backend/.env file)
docker-compose -f docker/docker-compose.yml exec postgres psql -U fitness_user -d fitness_bot
# Inside psql: \dt (list tables), \d users (describe table), \q (quit)

# Query data
# SELECT * FROM users LIMIT 5;
```

*Option 2: VS Code Extension (Recommended)*

1. **Install Extension**: Search for "PostgreSQL" by Chris Kolkman in VS Code Extensions (or similar like "SQLTools")

2. **Add Connection**:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Select "PostgreSQL: New Connection"
   - Enter connection details (find these in `backend/.env`):
     - **Host**: `localhost`
     - **Port**: `5432`
     - **Database**: `fitness_bot` (POSTGRES_DB in .env)
     - **Username**: `fitness_user` (POSTGRES_USER in .env)
     - **Password**: `fitness_pass_dev` (POSTGRES_PASSWORD in .env)
   - Save connection (e.g., name it "fitness-bot-local")

3. **Use Database**:
   - Click the PostgreSQL icon in the sidebar
   - Expand your connection to browse tables
   - Right-click tables to view data or schema
   - Create `.sql` files to run queries with syntax highlighting

**Reset Database** (deletes all data):
```powershell
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d postgres redis backend
docker-compose -f docker/docker-compose.yml exec backend alembic upgrade head
```

**Clear User Data for Testing Intake Agent** (preserves user account):

Useful for testing the intake specialist without needing to sign up again:

```powershell
# Get your user email (replace with yours)
$userEmail = "dev@example.com"

# Clear fitness plans, schedules, and conversation history (keeps account)
docker-compose -f docker/docker-compose.yml exec -T postgres psql -U fitness_user -d fitness_bot -c "
DELETE FROM schedule_entries WHERE schedule_id IN (SELECT id FROM schedules WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail'));
DELETE FROM schedules WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail');
DELETE FROM workouts WHERE workout_plan_id IN (SELECT id FROM workout_plans WHERE fitness_plan_id IN (SELECT id FROM fitness_plans WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail')));
DELETE FROM workout_plans WHERE fitness_plan_id IN (SELECT id FROM fitness_plans WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail'));
DELETE FROM meals WHERE meal_plan_id IN (SELECT id FROM meal_plans WHERE fitness_plan_id IN (SELECT id FROM fitness_plans WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail')));
DELETE FROM meal_plans WHERE fitness_plan_id IN (SELECT id FROM fitness_plans WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail'));
DELETE FROM phases WHERE fitness_plan_id IN (SELECT id FROM fitness_plans WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail'));
DELETE FROM fitness_plans WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail');
DELETE FROM conversations WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail');
DELETE FROM progress_records WHERE user_id = (SELECT id FROM users WHERE email = '$userEmail');
"

# Verify user still exists
docker-compose -f docker/docker-compose.yml exec -T postgres psql -U fitness_user -d fitness_bot -c "SELECT email, full_name, current_fitness_level FROM users WHERE email = '$userEmail';"
```

Now you can test the intake specialist from a fresh state without creating a new account!

**Redis Access**:
```powershell
# Redis CLI
docker-compose -f docker/docker-compose.yml exec redis redis-cli
# Inside redis-cli: KEYS * (list keys), GET key (get value), FLUSHALL (clear)

# Monitor real-time
docker-compose -f docker/docker-compose.yml exec redis redis-cli MONITOR
```

**Background Workers**:
```powershell
# View Celery logs
docker-compose -f docker/docker-compose.yml logs -f celery_worker

# Inspect tasks
docker-compose -f docker/docker-compose.yml exec backend celery -A src.workers.celery_app inspect active
```

---

## Troubleshooting

**Ports Already in Use**:
```powershell
# Check what's using ports
netstat -ano | findstr :3000
netstat -ano | findstr :8000
# Kill process or change ports in docker-compose.yml
```

**Database Connection Errors**:
```powershell
docker-compose -f docker/docker-compose.yml ps postgres
docker-compose -f docker/docker-compose.yml logs postgres
docker-compose -f docker/docker-compose.yml restart postgres
```

**Backend/Frontend Build Issues**:
```powershell
# Rebuild specific service
docker-compose -f docker/docker-compose.yml build backend
docker-compose -f docker/docker-compose.yml up -d backend

# Reinstall dependencies
docker-compose -f docker/docker-compose.yml exec backend pip install -r requirements.txt
docker-compose -f docker/docker-compose.yml exec frontend npm install
```

**OpenAI API Errors**:
```powershell
# Verify API key is set
docker-compose -f docker/docker-compose.yml exec backend env | Select-String OPENAI_API_KEY
```

**Hot Reload Not Working**: Check that `--reload` flag is in docker-compose.yml commands. On Windows, file watching should work by default.

---

## Quick Command Reference

Using the shorthand `$dc = "docker-compose -f docker/docker-compose.yml"`:

```powershell
# Service management
& $dc up -d                    # Start all services
& $dc down                     # Stop all services
& $dc ps                       # Check status
& $dc restart backend          # Restart service
& $dc up -d --build backend    # Rebuild and restart

# Logs and debugging
& $dc logs -f                  # All logs
& $dc logs -f backend          # Specific service logs
& $dc exec backend bash        # Access container shell
& $dc exec frontend sh         # Access frontend shell

# Destructive operations
& $dc down -v                  # Remove containers AND volumes (deletes data!)
& $dc pull                     # Pull latest images
```

---

## Timezone Detection & Handling

The application automatically detects and uses the client's timezone for all AI interactions:

**How It Works**:
- Frontend detects browser timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone`
- Timezone is sent during registration and login (IANA format: "America/New_York", "Europe/London", etc.)
- User's timezone is stored in the `users.timezone` database field
- All AI agents receive datetime context in user's local timezone:
  ```
  Current Date and Time: Saturday, December 07, 2025 at 01:20 PM (America/New_York)
  User Message: [user's message]
  ```

**Updating Timezone**:
```powershell
# PATCH /api/v1/users/me with timezone field
curl -X PATCH http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"timezone": "Asia/Tokyo"}'
```

**Per-Message Timezone Override** (optional):
```powershell
# Include timezone in message request to override user's stored timezone
curl -X POST http://localhost:8000/api/v1/ai/conversations/$conversationId/messages \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"message": "What should I eat for breakfast?", "timezone": "Europe/Paris"}'
```

**Implementation Files**:
- `frontend/src/lib/timezone.ts` - Browser timezone detection utilities
- `backend/src/models/user.py` - User model with timezone field
- `backend/src/services/ai_service.py` - Datetime context formatting
- `backend/src/api/v1/auth.py` - Registration/login with timezone
- `backend/src/api/v1/users.py` - Timezone update endpoint

---

## Next Steps & Resources

**Explore**:
- API docs: http://localhost:8000/docs
- Code entry points: `backend/src/main.py`, `frontend/src/app/page.tsx`

**Documentation**:
- Requirements: `/specs/001-ai-fitness-planner/spec.md`
- Architecture: `/specs/001-ai-fitness-planner/plan.md`
- Database schema: `/specs/001-ai-fitness-planner/data-model.md`
- API contracts: `/specs/001-ai-fitness-planner/contracts/api-contracts.md`

**Best Practices**:
- Run tests before committing: `pytest` and `npm test`
- Lint code before pushing: `ruff`, `eslint`
- Follow TDD: write tests first
- Use type hints (Python) and strict mode (TypeScript)
- Make small, focused commits with clear messages

---

## Quick Verification Script

```powershell
# test-setup.ps1
Write-Host "Testing backend health..."
curl -s http://localhost:8000/health

Write-Host "`nTesting frontend..."
$response = curl -s http://localhost:3000
if ($response -match "html") { Write-Host "✓ Frontend responding" }

Write-Host "`nTesting database..."
# Uses credentials from backend/.env file
docker-compose -f docker/docker-compose.yml exec -T postgres psql -U fitness_user -d fitness_bot -c "SELECT version();"

Write-Host "`nTesting Redis..."
docker-compose -f docker/docker-compose.yml exec -T redis redis-cli PING

Write-Host "`nAll services are running!"
```

---

## Summary

You now have a fully functional development environment:

✅ Backend API (FastAPI) - http://localhost:8000  
✅ Frontend App (Next.js) - http://localhost:3000  
✅ PostgreSQL Database - localhost:5432  
✅ Redis Cache/Queue - localhost:6379  
✅ Celery Background Workers  
✅ Interactive API docs - http://localhost:8000/docs  
✅ Hot reload on code changes  
✅ Full test suite configured  

**Happy coding! 🏋️‍♀️💪**
