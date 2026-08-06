"""
PANDORA User Service Unit Tests - Security
"""
import pytest
from datetime import timedelta
from jose import jwt

from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_access_token,
    validate_refresh_token,
)
from src.core.config import settings

pytestmark = pytest.mark.unit


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Test hash_password returns a string."""
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test hash_password returns different hashes for same password."""
        password = "SecurePass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # bcrypt includes salt, so hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password returns False for incorrect password."""
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert verify_password("WrongPassword123!", hashed) is False

    def test_verify_password_empty(self):
        """Test verify_password handles empty password."""
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token_returns_string(self):
        """Test create_access_token returns a JWT string."""
        token = create_access_token({
            "sub": "user-123",
            "email": "test@example.com",
            "role": "learner",
        })
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_payload(self):
        """Test access token contains expected payload."""
        token = create_access_token({
            "sub": "user-123",
            "email": "test@example.com",
            "role": "learner",
        })
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "learner"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_custom_expiry(self):
        """Test access token with custom expiry."""
        token = create_access_token(
            {"sub": "user-123"},
            expires_delta=timedelta(minutes=30),
        )
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert "exp" in payload

    def test_create_refresh_token_returns_string(self):
        """Test create_refresh_token returns a JWT string."""
        token = create_refresh_token({
            "sub": "user-123",
            "email": "test@example.com",
            "role": "learner",
        })
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_has_correct_type(self):
        """Test refresh token has type='refresh'."""
        token = create_refresh_token({
            "sub": "user-123",
        })
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self):
        """Test decode_token works with valid token."""
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"

    def test_decode_token_invalid(self):
        """Test decode_token raises error for invalid token."""
        with pytest.raises(Exception):
            decode_token("invalid.token.here")

    def test_validate_access_token_valid(self):
        """Test validate_access_token works with valid access token."""
        token = create_access_token({"sub": "user-123"})
        payload = validate_access_token(token)
        assert payload["sub"] == "user-123"

    def test_validate_access_token_wrong_type(self):
        """Test validate_access_token raises for refresh token."""
        token = create_refresh_token({"sub": "user-123"})
        with pytest.raises(Exception):
            validate_access_token(token)

    def test_validate_refresh_token_valid(self):
        """Test validate_refresh_token works with valid refresh token."""
        token = create_refresh_token({"sub": "user-123"})
        payload = validate_refresh_token(token)
        assert payload["sub"] == "user-123"

    def test_validate_refresh_token_wrong_type(self):
        """Test validate_refresh_token raises for access token."""
        token = create_access_token({"sub": "user-123"})
        with pytest.raises(Exception):
            validate_refresh_token(token)
