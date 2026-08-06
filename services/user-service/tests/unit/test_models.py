"""
PANDORA User Service Unit Tests - Models
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.models.user import User, Institution, LearningProfile, Session, UserRole
from src.models.verification import VerificationToken
from src.core.security import hash_password

pytestmark = pytest.mark.unit


class TestUserRole:
    """Tests for UserRole enum."""

    def test_user_role_values(self):
        """Test all user role values exist."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.INSTITUTION_ADMIN.value == "institution_admin"
        assert UserRole.INSTRUCTOR.value == "instructor"
        assert UserRole.LEARNER.value == "learner"
        assert UserRole.GUEST.value == "guest"

    def test_user_role_is_string(self):
        """Test user roles are strings."""
        for role in UserRole:
            assert isinstance(role.value, str)


class TestVerificationToken:
    """Tests for VerificationToken model."""

    def test_token_types(self):
        """Test token type constants."""
        assert VerificationToken.TokenType.EMAIL_VERIFICATION == "email_verification"
        assert VerificationToken.TokenType.PASSWORD_RESET == "password_reset"
        assert VerificationToken.TokenType.MFA_SETUP == "mfa_setup"

    def test_is_expired_false(self):
        """Test is_expired returns False for future date."""
        token = VerificationToken(
            user_id=uuid4(),
            token="test_token",
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert token.is_expired is False

    def test_is_expired_true(self):
        """Test is_expired returns True for past date."""
        token = VerificationToken(
            user_id=uuid4(),
            token="test_token",
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert token.is_expired is True

    def test_is_valid_true(self):
        """Test is_valid returns True for unused non-expired token."""
        token = VerificationToken(
            user_id=uuid4(),
            token="test_token",
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=False,
        )
        assert token.is_valid is True

    def test_is_valid_false_used(self):
        """Test is_valid returns False for used token."""
        token = VerificationToken(
            user_id=uuid4(),
            token="test_token",
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=True,
        )
        assert token.is_valid is False

    def test_is_valid_false_expired(self):
        """Test is_valid returns False for expired token."""
        token = VerificationToken(
            user_id=uuid4(),
            token="test_token",
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_used=False,
        )
        assert token.is_valid is False


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """Test creating a user instance."""
        user = User(
            email="test@example.com",
            password_hash=hash_password("SecurePass123!"),
            full_name="Test User",
            role=UserRole.LEARNER,
        )
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.LEARNER
        assert user.is_verified is False
        assert user.mfa_enabled is False

    def test_user_default_role(self):
        """Test user default role is LEARNER."""
        user = User(
            email="test@example.com",
            password_hash=hash_password("SecurePass123!"),
            full_name="Test User",
        )
        assert user.role == UserRole.LEARNER

    def test_user_institution_relationship(self):
        """Test user-institution relationship."""
        institution = Institution(
            name="Test University",
            domain="test.edu",
        )
        user = User(
            email="test@example.com",
            password_hash=hash_password("SecurePass123!"),
            full_name="Test User",
            institution=institution,
        )
        assert user.institution == institution
        assert user in institution.users


class TestInstitutionModel:
    """Tests for Institution model."""

    def test_institution_creation(self):
        """Test creating an institution instance."""
        institution = Institution(
            name="Test University",
            domain="test.edu",
            tier="free",
        )
        assert institution.name == "Test University"
        assert institution.domain == "test.edu"
        assert institution.tier == "free"

    def test_institution_default_tier(self):
        """Test institution default tier."""
        institution = Institution(
            name="Test University",
            domain="test.edu",
        )
        assert institution.tier == "free"


class TestLearningProfileModel:
    """Tests for LearningProfile model."""

    def test_learning_profile_creation(self):
        """Test creating a learning profile."""
        user_id = uuid4()
        profile = LearningProfile(
            user_id=user_id,
            education_level="undergraduate",
            learning_style="visual",
        )
        assert profile.user_id == user_id
        assert profile.education_level == "undergraduate"
        assert profile.learning_style == "visual"

    def test_knowledge_state_default(self):
        """Test knowledge state defaults to empty dict."""
        profile = LearningProfile(
            user_id=uuid4(),
            education_level="undergraduate",
            learning_style="mixed",
        )
        assert profile.knowledge_state == {}

    def test_knowledge_state_update(self):
        """Test updating knowledge state."""
        profile = LearningProfile(
            user_id=uuid4(),
            education_level="undergraduate",
            learning_style="mixed",
            knowledge_state={"math": {"level": 3, "mastery": 0.8}},
        )
        assert profile.knowledge_state["math"]["level"] == 3
        assert profile.knowledge_state["math"]["mastery"] == 0.8


class TestSessionModel:
    """Tests for Session model."""

    def test_session_creation(self):
        """Test creating a session."""
        user_id = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        session = Session(
            user_id=user_id,
            token_hash="hash123",
            expires_at=expires_at,
        )
        assert session.user_id == user_id
        assert session.token_hash == "hash123"
        assert session.is_revoked is False

    def test_session_default_not_revoked(self):
        """Test session default is not revoked."""
        session = Session(
            user_id=uuid4(),
            token_hash="hash123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        assert session.is_revoked is False
