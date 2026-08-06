"""
PANDORA User Service Unit Tests - conftest.py
Pytest fixtures and configuration
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.core.security import create_access_token, hash_password


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_id() -> str:
    """Generate a test user ID."""
    return str(uuid4())


@pytest.fixture
def test_email() -> str:
    """Generate a test email."""
    return f"test-{uuid4()}@example.com"


@pytest.fixture
def test_password() -> str:
    """Return test password."""
    return "SecurePass123!"


@pytest.fixture
def hashed_password() -> str:
    """Return a hashed password."""
    return hash_password("SecurePass123!")


@pytest.fixture
def valid_access_token(test_user_id: str, test_email: str) -> str:
    """Generate a valid access token for testing."""
    return create_access_token(
        data={
            "sub": test_user_id,
            "email": test_email,
            "role": "learner",
        },
        expires_delta=timedelta(minutes=15),
    )


@pytest.fixture
def auth_headers(valid_access_token: str) -> dict:
    """Generate auth headers with valid token."""
    return {"Authorization": f"Bearer {valid_access_token}"}


@pytest.fixture
def sample_user_data(test_email: str, test_password: str) -> dict:
    """Generate sample user registration data."""
    return {
        "email": test_email,
        "password": test_password,
        "full_name": "Test User",
        "role": "learner",
    }


@pytest.fixture
def sample_learning_profile() -> dict:
    """Generate sample learning profile data."""
    return {
        "education_level": "undergraduate",
        "target_education_level": "graduate",
        "learning_style": "visual",
        "preferred_content_types": ["video", "interactive"],
        "knowledge_state": {
            "mathematics": {"level": 3, "mastery": 0.7},
            "programming": {"level": 2, "mastery": 0.5},
        },
    }


@pytest.fixture
def sample_preferences() -> dict:
    """Generate sample preferences data."""
    return {
        "language": "en",
        "theme": "dark",
        "notifications": {
            "email": True,
            "push": True,
            "reminders": True,
        },
        "display": {
            "compact_mode": False,
            "show_progress": True,
        },
    }


class MockUser:
    """Mock user for testing."""

    def __init__(
        self,
        user_id: str | None = None,
        email: str | None = None,
        full_name: str = "Test User",
        role: str = "learner",
    ):
        self.id = user_id or str(uuid4())
        self.email = email or f"{uuid4()}@example.com"
        self.full_name = full_name
        self.role = role
        self.password_hash = hash_password("SecurePass123!")
        self.is_verified = True
        self.mfa_enabled = False
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


@pytest.fixture
def mock_user(test_user_id: str, test_email: str) -> MockUser:
    """Create a mock user."""
    return MockUser(user_id=test_user_id, email=test_email)
