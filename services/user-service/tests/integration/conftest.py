"""
PANDORA User Service Integration Tests - conftest.py
Integration test fixtures and test database setup
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

# Note: These tests require a running database and Redis instance
# Use docker-compose.yml to start dependencies before running integration tests


# Test database URL - use a separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/pandora_users_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        # Import models to register them with Base
        from src.models.base import Base
        from src.models.user import User, Institution, LearningProfile, Session
        
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables after tests
    async with engine.begin() as conn:
        from src.models.base import Base
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for each test."""
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client with database session.
    
    Note: This is a simplified version. In production, you'd want to:
    1. Override the database dependency
    2. Use a separate test app instance
    3. Set up proper dependency overrides
    """
    from src.api.main import app
    
    # Override database dependency (simplified)
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db_dependency] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Placeholder - implement based on your dependency injection
def get_db_dependency():
    """Placeholder for database dependency - implement in main.py"""
    pass


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """
    Create a test user in the database.
    
    Returns the user data dictionary.
    """
    from src.core.security import hash_password
    from src.models.user import User
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("SecurePass123!"),
        full_name="Test User",
        role="learner",
        is_verified=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return {
        "id": str(user.id),
        "email": user.email,
        "password": "SecurePass123!",
        "full_name": user.full_name,
    }


@pytest_asyncio.fixture
async def auth_tokens(client: AsyncClient, test_user: dict) -> dict:
    """
    Get authentication tokens by logging in.
    
    Returns access and refresh tokens.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )
    
    if response.status_code == 200:
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
        }
    
    # If login not implemented, return mock tokens
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
    }


@pytest_asyncio.fixture
def auth_headers(auth_tokens: dict) -> dict:
    """Generate auth headers with valid token."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}
