"""
PANDORA Quiz Service Unit Tests - Assessment Models
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from src.models import (
    Assessment,
    AssessmentStatus,
    AssessmentType,
    GradingType,
    AssessmentQuestion,
    AssessmentQuestionType,
    AssessmentQuestionDifficulty,
    BloomLevel,
    AssessmentAttempt,
    AttemptStatus,
    Answer,
)

pytestmark = pytest.mark.unit


class TestAssessmentModel:
    """Tests for Assessment model."""

    def test_assessment_creation(self):
        """Test assessment model creation."""
        assessment = Assessment(
            title="Final Exam",
            description="End of semester exam",
            assessment_type=AssessmentType.EXAM,
            passing_score=70.0,
            status=AssessmentStatus.DRAFT,
            question_count=0,
        )
        
        assert assessment.title == "Final Exam"
        assert assessment.description == "End of semester exam"
        assert assessment.assessment_type == AssessmentType.EXAM
        assert assessment.passing_score == 70.0
        assert assessment.status == AssessmentStatus.DRAFT
        assert assessment.question_count == 0

    def test_assessment_defaults(self):
        """Test assessment default values."""
        assessment = Assessment(
            title="Test Assessment",
            status=AssessmentStatus.DRAFT,
            assessment_type=AssessmentType.QUIZ,
            grading_type=GradingType.AUTOMATIC,
            allowed_attempts=1,
            passing_score=60.0,
            max_score=100.0,
            show_correct_answers=True,
            show_explanations=True,
            shuffle_questions=False,
            allow_back_navigation=True,
            allow_skip=True,
        )
        
        assert assessment.status == AssessmentStatus.DRAFT
        assert assessment.assessment_type == AssessmentType.QUIZ
        assert assessment.grading_type == GradingType.AUTOMATIC
        assert assessment.allowed_attempts == 1
        assert assessment.passing_score == 60.0
        assert assessment.max_score == 100.0
        assert assessment.show_correct_answers is True
        assert assessment.show_explanations is True
        assert assessment.shuffle_questions is False
        assert assessment.allow_back_navigation is True
        assert assessment.allow_skip is True

    def test_assessment_is_available(self):
        """Test is_available property."""
        # Published assessment without date restrictions
        assessment = Assessment(
            title="Test",
            status=AssessmentStatus.PUBLISHED,
            available_from=None,
            available_until=None,
        )
        assert assessment.is_available is True
        
        # Future assessment (using timezone-aware datetime)
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        assessment_future = Assessment(
            title="Future Test",
            status=AssessmentStatus.PUBLISHED,
            available_from=future_time,
        )
        assert assessment_future.is_available is False
        
        # Expired assessment
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        assessment_expired = Assessment(
            title="Expired Test",
            status=AssessmentStatus.PUBLISHED,
            available_until=past_time,
        )
        assert assessment_expired.is_available is False

    def test_assessment_is_open(self):
        """Test is_open property."""
        assessment = Assessment(
            title="Test",
            status=AssessmentStatus.PUBLISHED,
            question_count=5,
        )
        assert assessment.is_open is True
        
        # Assessment with no questions
        assessment_empty = Assessment(
            title="Empty Test",
            status=AssessmentStatus.PUBLISHED,
            question_count=0,
        )
        assert assessment_empty.is_open is False

    def test_assessment_repr(self):
        """Test assessment string representation."""
        assessment = Assessment(title="Test Exam")
        repr_str = repr(assessment)
        assert "Assessment" in repr_str
        assert "Test Exam" in repr_str


class TestAssessmentQuestionModel:
    """Tests for AssessmentQuestion model."""

    def test_question_creation(self):
        """Test question model creation."""
        question = AssessmentQuestion(
            stem="What is Python?",
            question_text="What is Python?",
            question_type=AssessmentQuestionType.MULTIPLE_CHOICE,
            points=2.0,
            difficulty=0.0,
            is_active=True,
        )
        
        assert question.stem == "What is Python?"
        assert question.question_text == "What is Python?"
        assert question.question_type == AssessmentQuestionType.MULTIPLE_CHOICE
        assert question.points == 2.0
        assert question.difficulty == 0.0
        assert question.is_active is True

    def test_question_options(self):
        """Test question with options."""
        options = [
            {"id": "a", "text": "A programming language", "is_correct": True},
            {"id": "b", "text": "A snake", "is_correct": False},
            {"id": "c", "text": "A game", "is_correct": False},
        ]
        correct_answer = {"type": "single", "value": "a"}
        
        question = AssessmentQuestion(
            stem="What is Python?",
            question_text="What is Python?",
            question_type=AssessmentQuestionType.MULTIPLE_CHOICE,
            options=options,
            correct_answer=correct_answer,
        )
        
        assert len(question.options) == 3
        assert question.correct_answer["value"] == "a"

    def test_question_statistics(self):
        """Test question statistics calculation."""
        question = AssessmentQuestion(
            stem="Test question",
            question_text="Test question",
            question_type=AssessmentQuestionType.MULTIPLE_CHOICE,
            times_shown=100,
            times_correct=75,
        )
        
        assert question.success_rate_calc == 0.75

    def test_question_update_statistics(self):
        """Test question statistics update method."""
        question = AssessmentQuestion(
            stem="Test question",
            question_text="Test question",
            question_type=AssessmentQuestionType.MULTIPLE_CHOICE,
            times_shown=50,
            times_correct=40,
        )
        
        question.update_statistics()
        
        assert question.success_rate == 0.8


class TestAssessmentAttemptModel:
    """Tests for AssessmentAttempt model."""

    def test_attempt_creation(self):
        """Test attempt model creation."""
        attempt = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
            status=AttemptStatus.NOT_STARTED,
            current_question_index=0,
            correct_answers=0,
            incorrect_answers=0,
        )
        
        assert attempt.status == AttemptStatus.NOT_STARTED
        assert len(attempt.question_ids) == 3
        assert attempt.current_question_index == 0
        assert attempt.correct_answers == 0
        assert attempt.incorrect_answers == 0

    def test_attempt_progress(self):
        """Test attempt progress calculation."""
        attempt = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
            answered_questions=[],
        )
        
        # No questions answered
        assert attempt.progress_percentage == 0.0
        
        # 2 questions answered
        attempt.answered_questions = [uuid.uuid4(), uuid.uuid4()]
        assert attempt.progress_percentage == 50.0

    def test_attempt_is_timed_out(self):
        """Test attempt timeout check."""
        # Attempt without time limit
        attempt_no_limit = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            time_limit_minutes=None,
        )
        assert attempt_no_limit.is_timed_out is False
        
        # Recent attempt
        attempt_recent = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            time_limit_minutes=30,
            started_at=datetime.now(timezone.utc),
        )
        assert attempt_recent.is_timed_out is False

    def test_attempt_remaining_time(self):
        """Test remaining time calculation."""
        # No limit
        attempt_no_limit = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
        )
        assert attempt_no_limit.remaining_time_seconds is None
        
        # With time limit (just started)
        attempt_started = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            time_limit_minutes=30,
            started_at=datetime.now(timezone.utc),
        )
        remaining = attempt_started.remaining_time_seconds
        assert remaining is not None
        assert remaining <= 1800  # 30 minutes in seconds
        assert remaining > 0

    def test_attempt_can_submit(self):
        """Test attempt submit check."""
        attempt_in_progress = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            status=AttemptStatus.IN_PROGRESS,
        )
        assert attempt_in_progress.can_submit is True
        
        # Expired attempt
        past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        attempt_expired = AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            status=AttemptStatus.IN_PROGRESS,
            time_limit_minutes=30,
            started_at=past_time,
        )
        assert attempt_expired.can_submit is False

    def test_attempt_is_complete(self):
        """Test attempt completion check."""
        assert AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            status=AttemptStatus.SUBMITTED,
        ).is_complete is True
        
        assert AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            status=AttemptStatus.GRADED,
        ).is_complete is True
        
        assert AssessmentAttempt(
            assessment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question_ids=[],
            status=AttemptStatus.IN_PROGRESS,
        ).is_complete is False


class TestAnswerModel:
    """Tests for Answer model."""

    def test_answer_creation(self):
        """Test answer model creation."""
        answer = Answer(
            attempt_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            sequence_number=1,
            points_earned=0.0,
            is_skipped=False,
            is_flagged=False,
        )
        
        assert answer.attempt_id is not None
        assert answer.question_id is not None
        assert answer.sequence_number == 1
        assert answer.points_earned == 0.0
        assert answer.is_skipped is False
        assert answer.is_flagged is False

    def test_answer_mark_correct(self):
        """Test marking answer as correct."""
        answer = Answer(
            attempt_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            sequence_number=1,
        )
        
        answer.mark_correct(points_earned=2.0)
        
        assert answer.is_correct is True
        assert answer.points_earned == 2.0
        assert answer.is_graded is True

    def test_answer_mark_incorrect(self):
        """Test marking answer as incorrect."""
        answer = Answer(
            attempt_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            sequence_number=1,
        )
        
        answer.mark_incorrect()
        
        assert answer.is_correct is False
        assert answer.points_earned == 0.0
        assert answer.is_graded is True

    def test_answer_mark_skipped(self):
        """Test marking answer as skipped."""
        answer = Answer(
            attempt_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            sequence_number=1,
            answer={"type": "single", "value": "a"},
        )
        
        answer.mark_skipped()
        
        assert answer.is_skipped is True
        assert answer.answer is None

    def test_answer_score_percentage(self):
        """Test score percentage calculation."""
        answer = Answer(
            attempt_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            sequence_number=1,
            points_earned=2.0,
            max_points=4.0,
        )
        
        assert answer.score_percentage == 50.0
        
        # Zero max points
        answer_zero = Answer(
            attempt_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            sequence_number=1,
            points_earned=0.0,
            max_points=0.0,
        )
        assert answer_zero.score_percentage is None


class TestAssessmentEnums:
    """Tests for assessment-related enums."""

    def test_assessment_status(self):
        """Test AssessmentStatus enum values."""
        assert AssessmentStatus.DRAFT.value == "draft"
        assert AssessmentStatus.PUBLISHED.value == "published"
        assert AssessmentStatus.ARCHIVED.value == "archived"
        assert AssessmentStatus.DELETED.value == "deleted"

    def test_assessment_type(self):
        """Test AssessmentType enum values."""
        assert AssessmentType.QUIZ.value == "quiz"
        assert AssessmentType.EXAM.value == "exam"
        assert AssessmentType.HOMEWORK.value == "homework"
        assert AssessmentType.PRACTICE.value == "practice"
        assert AssessmentType.PLACEMENT.value == "placement"

    def test_grading_type(self):
        """Test GradingType enum values."""
        assert GradingType.AUTOMATIC.value == "automatic"
        assert GradingType.MANUAL.value == "manual"
        assert GradingType.HYBRID.value == "hybrid"

    def test_attempt_status(self):
        """Test AttemptStatus enum values."""
        assert AttemptStatus.NOT_STARTED.value == "not_started"
        assert AttemptStatus.IN_PROGRESS.value == "in_progress"
        assert AttemptStatus.PAUSED.value == "paused"
        assert AttemptStatus.SUBMITTED.value == "submitted"
        assert AttemptStatus.GRADED.value == "graded"
        assert AttemptStatus.EXPIRED.value == "expired"
        assert AttemptStatus.ABANDONED.value == "abandoned"

    def test_question_type(self):
        """Test AssessmentQuestionType enum values."""
        assert AssessmentQuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert AssessmentQuestionType.MULTIPLE_SELECT.value == "multiple_select"
        assert AssessmentQuestionType.TRUE_FALSE.value == "true_false"
        assert AssessmentQuestionType.SHORT_ANSWER.value == "short_answer"
        assert AssessmentQuestionType.ESSAY.value == "essay"
        assert AssessmentQuestionType.FILE_UPLOAD.value == "file_upload"

    def test_bloom_level(self):
        """Test BloomLevel enum values."""
        assert BloomLevel.REMEMBER.value == "remember"
        assert BloomLevel.UNDERSTAND.value == "understand"
        assert BloomLevel.APPLY.value == "apply"
        assert BloomLevel.ANALYZE.value == "analyze"
        assert BloomLevel.EVALUATE.value == "evaluate"
        assert BloomLevel.CREATE.value == "create"
