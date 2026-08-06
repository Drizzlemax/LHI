"""
PANDORA User Service Authentication Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.security import (
    hash_password,
    verify_password,
)
from src.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPayload,
    MFASetupResponse,
    UserProfileResponse,
)
from src.services.user_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncSession:
    """Dependency to get database session."""
    async for session in get_db():
        yield session


def create_auth_response(user, access_token: str, refresh_token: str) -> AuthResponse:
    """Create AuthResponse from user and tokens."""
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_verified=user.is_verified,
            mfa_enabled=user.mfa_enabled,
        ),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """
    Register a new user account.
    
    Creates a new user with the provided credentials and returns
    access and refresh tokens.
    """
    auth_service = AuthService(db)
    
    # Check if email already exists
    existing_user = await auth_service.user_service.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    # Create user and get tokens
    user, access_token, refresh_token = await auth_service.register(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=request.role,
    )
    
    return create_auth_response(user, access_token, refresh_token)


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """
    Authenticate user and return tokens.
    
    Validates credentials and returns JWT access and refresh tokens.
    """
    auth_service = AuthService(db)
    
    # Get client info
    user_agent = http_request.headers.get("user-agent")
    ip_address = http_request.client.host if http_request.client else None
    
    # Authenticate user
    result = await auth_service.login(
        email=request.email,
        password=request.password,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user, access_token, refresh_token = result
    return create_auth_response(user, access_token, refresh_token)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """
    Refresh access token using refresh token.
    
    Validates the refresh token and issues a new access token.
    """
    auth_service = AuthService(db)
    
    result = await auth_service.refresh_tokens(request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token, refresh_token = result
    
    # Get user from token (decode to get user_id)
    from src.core.security import decode_token
    payload = decode_token(access_token)
    user_id = payload["sub"]
    
    # Get user
    user = await auth_service.user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return create_auth_response(user, access_token, refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Logout user by invalidating session.
    
    Revokes the current session and invalidates the token.
    """
    if not credentials:
        return  # No token provided, nothing to logout
    
    auth_service = AuthService(db)
    await auth_service.logout(credentials.credentials)


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> MFASetupResponse:
    """
    Set up Multi-Factor Authentication.
    
    Generates a TOTP secret and provisioning URI for authenticator apps.
    """
    # TODO: Implement MFA setup
    # For now, return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA setup not yet implemented. Please use email verification instead.",
    )


@router.post("/mfa/verify")
async def verify_mfa(
    code: str,
    token: str,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """
    Verify MFA code and complete authentication.
    
    Validates the TOTP code and returns full authentication tokens.
    """
    # TODO: Implement MFA verification
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA verification not yet implemented",
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> TokenPayload:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Extracts and validates the JWT token from the Authorization header.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        from src.core.security import validate_access_token
        payload = validate_access_token(credentials.credentials)
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
