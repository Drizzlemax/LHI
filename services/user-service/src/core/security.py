"""
PANDORA User Service Security Module
Password hashing, JWT token creation/validation, MFA verification
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {e}")


def validate_access_token(token: str) -> dict[str, Any]:
    """Validate an access token and return its payload."""
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise JWTError("Invalid token type: expected access token")

    return payload


def validate_refresh_token(token: str) -> dict[str, Any]:
    """Validate a refresh token and return its payload."""
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type: expected refresh token")

    return payload


# TODO: Implement MFA with TOTP
class MFAManager:
    """Manage Multi-Factor Authentication."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a TOTP secret."""
        # TODO: Implement with pyotp
        raise NotImplementedError("MFA not yet implemented")

    @staticmethod
    def get_provisioning_uri(secret: str, email: str) -> str:
        """Get the provisioning URI for authenticator apps."""
        # TODO: Implement with pyotp
        raise NotImplementedError("MFA not yet implemented")

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Verify a TOTP code."""
        # TODO: Implement with pyotp
        raise NotImplementedError("MFA not yet implemented")
