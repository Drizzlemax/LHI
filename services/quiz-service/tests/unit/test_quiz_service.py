"""
PANDORA Quiz Service Unit Tests - Quiz Service
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.quiz_service import QuizService
from src.schemas.quiz import QuizCreate, QuizUpdate

pytestmark = pytest.mark.unit


class TestQuizService:
    """Tests for QuizService."""

    def test_service_instantiation(self, mock_db_session: AsyncMock):
        """Test service can be instantiated."""
        service = QuizService(mock_db_session)
        assert service is not None
        assert isinstance(service, QuizService)
        assert service.db == mock_db_session

    def test_quiz_create_schema(self):
        """Test QuizCreate schema validation."""
        quiz_data = QuizCreate(
            title="Test Quiz",
            description="A test quiz",
            question_type="multiple_choice",
            time_limit_minutes=30,
            allowed_attempts=3,
            passing_score=70.0,
        )
        assert quiz_data.title == "Test Quiz"
        assert quiz_data.question_type == "multiple_choice"
        assert quiz_data.passing_score == 70.0

    def test_quiz_create_schema_defaults(self):
        """Test QuizCreate schema defaults."""
        quiz_data = QuizCreate(title="Test Quiz")
        assert quiz_data.description is None
        assert quiz_data.question_type == "multiple_choice"
        assert quiz_data.allowed_attempts == 3
        assert quiz_data.passing_score == 70.0
        assert quiz_data.is_adaptive is False

    def test_quiz_update_schema(self):
        """Test QuizUpdate schema with partial updates."""
        update_data = QuizUpdate(title="Updated Title")
        assert update_data.title == "Updated Title"
        assert update_data.description is None
        assert update_data.passing_score is None


class TestQuizModel:
    """Tests for Quiz model."""

    def test_quiz_creation(self, sample_quiz: MagicMock):
        """Test quiz model creation."""
        assert sample_quiz.title == "Introduction to Python"
        assert sample_quiz.status == "published"
        assert sample_quiz.is_adaptive is True
        assert sample_quiz.passing_score == 70.0

    def test_quiz_repr(self, sample_quiz: MagicMock):
        """Test quiz string representation."""
        repr_str = repr(sample_quiz)
        assert "Quiz" in repr_str


class TestQuestionModel:
    """Tests for Question model."""

    def test_question_creation(self, sample_question: MagicMock):
        """Test question model creation."""
        assert sample_question.stem == "What is Python?"
        assert sample_question.question_type == "multiple_choice"
        assert sample_question.difficulty == 0.5
        assert len(sample_question.options) == 3

    def test_question_correct_answer(self, sample_question: MagicMock):
        """Test question correct answer format."""
        assert sample_question.correct_answer["type"] == "single"
        assert sample_question.correct_answer["value"] == "b"


class TestSessionModel:
    """Tests for QuizSession model."""

    def test_session_creation(self, sample_session: MagicMock):
        """Test session model creation."""
        assert sample_session.status == "in_progress"
        assert sample_session.current_question_index == 0
        assert sample_session.estimated_ability == 0.0
        assert sample_session.ability_std == 1.0

    def test_session_progress(self, sample_session: MagicMock):
        """Test session progress calculation."""
        sample_session.question_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        sample_session.current_question_index = 1
        
        progress = sample_session.current_question_index / len(sample_session.question_ids)
        assert progress == pytest.approx(0.333, rel=0.01)
