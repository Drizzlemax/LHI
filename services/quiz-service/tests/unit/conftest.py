"""
PANDORA Quiz Service Unit Test Configuration
"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory
from src.models import Quiz, Question, QuizSession


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_quiz_id() -> uuid.UUID:
    """Sample quiz ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_question_id() -> uuid.UUID:
    """Sample question ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_session_id() -> uuid.UUID:
    """Sample session ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    """Sample user ID."""
    return uuid.uuid4()


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_quiz(sample_quiz_id: uuid.UUID, sample_user_id: uuid.UUID) -> MagicMock:
    """Create sample quiz mock."""
    quiz = MagicMock(spec=Quiz)
    quiz.id = sample_quiz_id
    quiz.title = "Introduction to Python"
    quiz.description = "Test your Python knowledge"
    quiz.status = "published"
    quiz.question_type = "multiple_choice"
    quiz.time_limit_minutes = 30
    quiz.allowed_attempts = 3
    quiz.passing_score = 70.0
    quiz.max_score = 100.0
    quiz.is_adaptive = True
    quiz.shuffle_questions = False
    quiz.question_ids = [uuid.uuid4(), uuid.uuid4()]
    quiz.created_at = datetime.now(timezone.utc)
    quiz.updated_at = datetime.now(timezone.utc)
    return quiz


@pytest.fixture
def sample_question(sample_question_id: uuid.UUID, sample_quiz_id: uuid.UUID) -> MagicMock:
    """Create sample question mock."""
    question = MagicMock(spec=Question)
    question.id = sample_question_id
    question.quiz_id = sample_quiz_id
    question.stem = "What is Python?"
    question.question_type = "multiple_choice"
    question.options = [
        {"id": "a", "text": "A snake", "is_correct": False},
        {"id": "b", "text": "A programming language", "is_correct": True},
        {"id": "c", "text": "A game", "is_correct": False},
    ]
    question.correct_answer = {"type": "single", "value": "b"}
    question.difficulty = 0.5
    question.discrimination = 1.0
    question.guessing_parameter = 0.25
    question.points = 1.0
    question.is_active = True
    question.created_at = datetime.now(timezone.utc)
    return question


@pytest.fixture
def sample_session(
    sample_session_id: uuid.UUID,
    sample_quiz_id: uuid.UUID,
    sample_user_id: uuid.UUID,
) -> MagicMock:
    """Create sample session mock."""
    session = MagicMock(spec=QuizSession)
    session.id = sample_session_id
    session.quiz_id = sample_quiz_id
    session.user_id = sample_user_id
    session.status = "in_progress"
    session.question_ids = [uuid.uuid4(), uuid.uuid4()]
    session.current_question_index = 0
    session.estimated_ability = 0.0
    session.ability_std = 1.0
    session.answered_questions = []
    session.flagged_questions = []
    session.started_at = datetime.now(timezone.utc)
    session.time_limit_minutes = 30
    return session
