"""FastAPI main application."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1 import ai_agent, auth, fitness_plans, users
from src.config import settings
from src.utils.cache import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.close()


# Create FastAPI application
app = FastAPI(
    title="Fitness Bot API",
    description="AI-Powered Fitness Planner API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred" if settings.ENVIRONMENT == "production" else str(exc),
            },
            "metadata": {
                "timestamp": None,
                "request_id": None,
            },
        },
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(fitness_plans.router, prefix="/api/v1/fitness-plans", tags=["fitness-plans"])
app.include_router(ai_agent.router, prefix="/api/v1/ai", tags=["ai"])
# app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])  # User Story 2
# app.include_router(progress.router, prefix="/api/v1/progress", tags=["progress"])  # User Story 2
# app.include_router(workouts.router, prefix="/api/v1/workouts", tags=["workouts"])  # User Story 4
