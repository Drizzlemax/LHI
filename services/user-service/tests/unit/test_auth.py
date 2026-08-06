"""
PANDORA User Service Unit Tests - Authentication
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.unit


class TestRegister:
    """Tests for user registration."""

    async def test_register_invalid_email(
        self,
        client: AsyncClient,
    ):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123!",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_weak_password(
        self,
        client: AsyncClient,
    ):
        """Test registration with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_missing_fields(
        self,
        client: AsyncClient,
    ):
        """Test registration with missing required fields."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    async def test_login_invalid_credentials(
        self,
        client: AsyncClient,
    ):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    async def test_login_missing_fields(
        self,
        client: AsyncClient,
    ):
        """Test login with missing fields."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
            },
        )
        assert response.status_code == 422


class TestRefresh:
    """Tests for token refresh."""

    async def test_refresh_invalid_token(
        self,
        client: AsyncClient,
    ):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    async def test_refresh_missing_token(
        self,
        client: AsyncClient,
    ):
        """Test refresh with missing token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        assert response.status_code == 422


class TestLogout:
    """Tests for user logout."""

    async def test_logout_without_auth(
        self,
        client: AsyncClient,
    ):
        """Test logout without authentication (should succeed - no token to revoke)."""
        response = await client.post("/api/v1/auth/logout")
        # Returns 204 because there's no token to invalidate
        assert response.status_code == 204


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_ready_check(self, client: AsyncClient):
        """Test readiness check endpoint."""
        response = await client.get("/ready")
        # May return 503 if DB is not connected
        assert response.status_code in [200, 503]


# Fixtures for refresh tests
@pytest.fixture
def valid_refresh_token(test_user_id: str, test_email: str) -> str:
    """Generate a valid refresh token."""
    from datetime import timedelta
    from src.core.security import create_refresh_token
    return create_refresh_token(
        data={
            "sub": test_user_id,
            "email": test_email,
            "role": "learner",
        },
        expires_delta=timedelta(days=7),
    )


@pytest.fixture
def expired_refresh_token(test_user_id: str, test_email: str) -> str:
    """Generate an expired refresh token."""
    from datetime import timedelta
    from src.core.security import create_refresh_token
    return create_refresh_token(
        data={
            "sub": test_user_id,
            "email": test_email,
            "role": "learner",
        },
        expires_delta=timedelta(days=-1),  # Already expired
    )
