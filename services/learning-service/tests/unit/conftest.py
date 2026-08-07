"""
PANDORA Learning Service Unit Test Fixtures
"""
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.models.base import Base
from src.models import (
    LearningPath,
    Module,
    PathLesson,
    UserProgress,
    UserLearningStats,
    LearningPathEnrollment,
    LearningPathStatus,
    ModuleStatus,
    LessonStatus,
    LessonType,
    ProgressStatus,
)
from src.core.database import get_db
from src.api.main import app


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def mock_db_session() -> AsyncMock:
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


# ============ Fixture Helpers ============

@pytest.fixture
def sample_user_id() -> uuid.UUID:
    """Generate sample user ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_path_id() -> uuid.UUID:
    """Generate sample path ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_module_id() -> uuid.UUID:
    """Generate sample module ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_lesson_id() -> uuid.UUID:
    """Generate sample lesson ID."""
    return uuid.uuid4()


# ============ Model Fixtures ============

@pytest.fixture
def sample_learning_path(sample_path_id: uuid.UUID, sample_user_id: uuid.UUID) -> MagicMock:
    """Create sample learning path mock."""
    path = MagicMock(spec=LearningPath)
    path.id = sample_path_id
    path.user_id = sample_user_id
    path.title = "Introduction to Python"
    path.description = "Learn Python basics"
    path.goal = "Master Python fundamentals"
    path.status = LearningPathStatus.DRAFT
    path.progress_percentage = 0.0
    path.is_public = False
    path.module_count = 0
    path.lesson_count = 0
    now = datetime.now(timezone.utc)
    path.created_at = now
    path.updated_at = now
    return path


@pytest.fixture
def sample_module(sample_module_id: uuid.UUID, sample_path_id: uuid.UUID) -> MagicMock:
    """Create sample module mock."""
    module = MagicMock(spec=Module)
    module.id = sample_module_id
    module.learning_path_id = sample_path_id
    module.title = "Getting Started"
    module.description = "Initial setup"
    module.order_index = 0
    module.status = ModuleStatus.LOCKED
    module.lesson_count = 0
    module.progress_percentage = 0.0
    now = datetime.now(timezone.utc)
    module.created_at = now
    module.updated_at = now
    return module


@pytest.fixture
def sample_lesson(sample_lesson_id: uuid.UUID, sample_module_id: uuid.UUID) -> MagicMock:
    """Create sample lesson mock."""
    lesson = MagicMock(spec=PathLesson)
    lesson.id = sample_lesson_id
    lesson.module_id = sample_module_id
    lesson.title = "Installing Python"
    lesson.description = "How to install Python"
    lesson.lesson_type = LessonType.VIDEO
    lesson.order_index = 0
    lesson.status = LessonStatus.LOCKED
    lesson.estimated_minutes = 15
    lesson.points = 10
    lesson.xp_reward = 50
    now = datetime.now(timezone.utc)
    lesson.created_at = now
    lesson.updated_at = now
    return lesson


@pytest.fixture
def sample_user_progress(
    sample_user_id: uuid.UUID,
    sample_lesson_id: uuid.UUID,
    sample_path_id: uuid.UUID,
    sample_module_id: uuid.UUID,
) -> MagicMock:
    """Create sample user progress mock."""
    progress = MagicMock(spec=UserProgress)
    progress.id = uuid.uuid4()
    progress.user_id = sample_user_id
    progress.lesson_id = sample_lesson_id
    progress.learning_path_id = sample_path_id
    progress.module_id = sample_module_id
    progress.status = ProgressStatus.IN_PROGRESS
    progress.progress_percentage = 50.0
    progress.time_spent_seconds = 300
    now = datetime.now(timezone.utc)
    progress.created_at = now
    progress.updated_at = now
    progress.started_at = now
    return progress


@pytest.fixture
def sample_user_stats(sample_user_id: uuid.UUID) -> MagicMock:
    """Create sample user stats mock."""
    stats = MagicMock(spec=UserLearningStats)
    stats.id = uuid.uuid4()
    stats.user_id = sample_user_id
    stats.lessons_completed = 5
    stats.quizzes_passed = 3
    stats.quizzes_failed = 1
    stats.paths_enrolled = 2
    stats.paths_completed = 0
    stats.total_time_seconds = 3600
    stats.total_xp = 500
    stats.current_streak_days = 3
    stats.longest_streak_days = 7
    now = datetime.now(timezone.utc)
    stats.created_at = now
    stats.updated_at = now
    return stats


# ============ Async Client Fixture ============

@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")

    yield client

    client.close()
    app.dependency_overrides.clear()


# ============ Mock Neo4j Fixture ============

@pytest.fixture
def mock_neo4j_client() -> MagicMock:
    """Create mock Neo4j client."""
    client = MagicMock()
    client.execute_query = AsyncMock(return_value=[])
    client.execute_write = AsyncMock(return_value={"counters": {}})
    client.get_user_learning_history = AsyncMock(return_value=[])
    client.get_content_prerequisites = AsyncMock(return_value=[])
    client.record_content_completion = AsyncMock(return_value=True)
    return client
