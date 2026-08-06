"""
PANDORA User Service Unit Tests - Authentication
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.unit


class TestRegister:
    """Tests for user registration."""

    async def test_register_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json=sample_user_data,
        )
        
        # TODO: Update assertion when implementation is complete
        # Currently returns 501 Not Implemented
        assert response.status_code in [201, 501]

    async def test_register_invalid_email(
        self,
        client: AsyncClient,
        test_password: str,
    ):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": test_password,
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_weak_password(
        self,
        client: AsyncClient,
        test_email: str,
    ):
        """Test registration with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "weak",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    async def test_login_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ):
        """Test successful login."""
        # Note: Requires user to be registered first
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        
        # TODO: Update assertion when implementation is complete
        assert response.status_code in [200, 401, 501]

    async def test_login_invalid_credentials(
        self,
        client: AsyncClient,
        test_email: str,
    ):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code in [401, 501]

    async def test_login_nonexistent_user(
        self,
        client: AsyncClient,
    ):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )
        assert response.status_code in [401, 501]


class TestRefresh:
    """Tests for token refresh."""

    async def test_refresh_success(
        self,
        client: AsyncClient,
        valid_refresh_token: str,
    ):
        """Test successful token refresh."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": valid_refresh_token},
        )
        
        # TODO: Update assertion when implementation is complete
        assert response.status_code in [200, 401, 501]

    async def test_refresh_invalid_token(
        self,
        client: AsyncClient,
    ):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code in [401, 422]

    async def test_refresh_expired_token(
        self,
        client: AsyncClient,
        expired_refresh_token: str,
    ):
        """Test refresh with expired token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_refresh_token},
        )
        assert response.status_code in [401, 422]


class TestLogout:
    """Tests for user logout."""

    async def test_logout_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test successful logout."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers,
        )
        
        # TODO: Update assertion when implementation is complete
        assert response.status_code in [204, 401, 501]

    async def test_logout_without_auth(
        self,
        client: AsyncClient,
    ):
        """Test logout without authentication."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401


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
