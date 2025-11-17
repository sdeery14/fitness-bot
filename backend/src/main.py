"""FastAPI main application."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1 import ai_agent, auth, fitness_plans, progress, schedules, users
from src.config import settings
from src.middleware.logging_middleware import LoggingMiddleware
from src.middleware.rate_limit_middleware import RateLimitMiddleware
from src.schemas import create_error_response
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
    redirect_slashes=False,  # Disable automatic redirect for trailing slashes
)

# Middleware stack (executed in reverse order of registration)
# 1. Logging middleware (outermost - logs all requests)
app.add_middleware(LoggingMiddleware)

# 2. Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# 3. CORS middleware
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
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper error response format."""
    # If detail is already a dict (our error response), return it
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    
    # Map status codes to error codes
    error_code = "HTTP_ERROR"
    if exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 400:
        error_code = "BAD_REQUEST"
    elif exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
    elif exc.status_code == 409:
        error_code = "CONFLICT"
    
    # Create error response
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code=error_code,
            message=str(exc.detail),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with proper error response format."""
    # Get first error for simplicity
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")
    
    return JSONResponse(
        status_code=400,
        content=create_error_response(
            code="VALIDATION_ERROR",
            message=message,
            field=field if field else None,
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred" if settings.ENVIRONMENT == "production" else str(exc),
        ),
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
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])  # User Story 2
app.include_router(progress.router, prefix="/api/v1/progress", tags=["progress"])  # User Story 2
# app.include_router(workouts.router, prefix="/api/v1/workouts", tags=["workouts"])  # User Story 4
