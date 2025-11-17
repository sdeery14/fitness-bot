"""API v1 router configuration."""
from fastapi import APIRouter

from src.api.v1 import ai_agent, auth, fitness_plans, users, workouts

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    fitness_plans.router, prefix="/fitness-plans", tags=["fitness-plans"]
)
api_router.include_router(ai_agent.router, prefix="/ai", tags=["ai-agent"])
api_router.include_router(workouts.router, tags=["workouts"])
