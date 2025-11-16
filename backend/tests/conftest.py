"""Pytest configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.api.deps import get_db
from src.config import settings
from src.database import Base
from src.main import app
from src.models import *  # noqa: F401, F403 - Import all models to create tables
from src.models.user import User  # Explicit import for type hints

# Test database URL (override settings)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/fitness_bot", "/fitness_bot_test")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create async engine for test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable connection pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for tests.
    Each test gets a fresh session with transaction rollback.
    """
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for anyio tests."""
    return "asyncio"


@pytest_asyncio.fixture
async def async_client(engine):
    """Create async HTTP client for API testing."""
    from httpx import ASGITransport

    # Override database dependency
    async def override_get_db():
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(engine):
    """Create a test user for auth tests."""
    from src.services.auth_service import AuthService
    from src.services.user_service import UserService

    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        user_service = UserService(session)
        
        # Check if user already exists
        existing_user = await user_service.get_user_by_email("testuser@example.com")
        
        if existing_user:
            # Return existing user
            yield existing_user
        else:
            # Create new user
            auth_service = AuthService(session)
            user = await auth_service.register(
                email="testuser@example.com",
                password="testpass123",
                name="Test User",
                date_of_birth="1990-01-01",
                fitness_level="intermediate",
            )
            await session.commit()
            await session.refresh(user)
            
            # Return user
            yield user


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, test_user: User) -> dict:
    """Create authenticated user and return auth headers using test_user."""
    # Login as test_user (testuser@example.com)
    login_payload = {
        "email": "testuser@example.com",
        "password": "testpass123"
    }

    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200, f"Login failed: {response.json()}"

    data = response.json()
    token = data["data"]["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_conversation(engine, test_user):
    """Create a test conversation for AI agent tests."""
    from src.services.conversation_service import ConversationService

    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        conversation_service = ConversationService(session)
        conversation = await conversation_service.create_conversation(
            user_id=test_user.id,
            conversation_type="plan_creation",
        )
        await session.commit()
        await session.refresh(conversation)
        yield conversation


@pytest_asyncio.fixture
async def test_fitness_plan(engine, test_user):
    """Create a test fitness plan for plan tests."""
    from src.services.plan_service import PlanService

    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        plan_service = PlanService(session)
        plan = await plan_service.create_plan(
            user_id=test_user.id,
            goal="weight_loss",
            requirements={"goal_description": "Test goal", "test": True},
            duration_weeks=12,
        )
        # Set plan to active status for tests that need an active plan
        plan.status = "active"
        await session.commit()
        await session.refresh(plan)
        yield plan
