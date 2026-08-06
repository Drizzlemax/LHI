"""
PANDORA User Service Auth Schemas
Pydantic models for authentication endpoints
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    full_name: str = Field(..., min_length=1, max_length=100, description="Full name")
    role: str = Field(default="learner", description="User role")
    institution_id: UUID | None = Field(default=None, description="Institution ID")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "student@university.edu",
                "password": "SecurePass123!",
                "full_name": "Jane Doe",
                "role": "learner",
            }
        }
    }


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "student@university.edu",
                "password": "SecurePass123!",
            }
        }
    }


class RefreshRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    }


class AuthResponse(BaseModel):
    """Response schema for authentication operations."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    user: "UserProfileResponse"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "student@university.edu",
                    "full_name": "Jane Doe",
                    "role": "learner",
                    "is_verified": False,
                    "mfa_enabled": False,
                },
            }
        }
    }


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    type: str = Field(..., description="Token type (access/refresh)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")


class MFASetupResponse(BaseModel):
    """Response schema for MFA setup."""

    provisioning_uri: str = Field(..., description="TOTP provisioning URI")
    backup_codes: list[str] = Field(..., description="Backup codes for recovery")
    secret: str = Field(..., description="TOTP secret (show once)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "provisioning_uri": "otpauth://totp/PANDORA:jane@example.com?secret=JBSWY3DPEHPK3PXP&issuer=PANDORA",
                "backup_codes": ["abc123", "def456", "ghi789"],
                "secret": "JBSWY3DPEHPK3PXP",
            }
        }
    }


class UserProfileResponse(BaseModel):
    """Response schema for user profile."""

    id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role")
    avatar_url: str | None = Field(default=None, description="Avatar URL")
    institution: "InstitutionSummary | None" = Field(default=None)
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_verified: bool = Field(..., description="Email verification status")
    mfa_enabled: bool = Field(..., description="MFA enabled status")


class InstitutionSummary(BaseModel):
    """Summary schema for institution."""

    id: UUID = Field(..., description="Institution unique identifier")
    name: str = Field(..., description="Institution name")
    domain: str = Field(..., description="Institution domain")


# Update forward references
AuthResponse.model_rebuild()
UserProfileResponse.model_rebuild()
