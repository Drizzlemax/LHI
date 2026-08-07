"""
PANDORA Quiz Service Session Management Service
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import QuizSession, QuizSessionStatus, Quiz, QuizStatus, Question
from src.schemas.session import SessionStart


class SessionService:
    """Service for quiz session management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(self, session_data: SessionStart) -> QuizSession:
        """Create a new quiz session."""
        session = QuizSession(
            quiz_id=session_data.quiz_id,
            user_id=session_data.user_id,
            status=QuizSessionStatus.NOT_STARTED,
            question_ids=[],
            estimated_ability=0.0,
            ability_std=1.0,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def start_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """Start a quiz session."""
        session = await self.get_session(session_id)
        if not session or session.status != QuizSessionStatus.NOT_STARTED:
            return None
        
        # Get quiz
        quiz = await self._get_quiz(session.quiz_id)
        if not quiz or quiz.status != QuizStatus.PUBLISHED:
            return None
        
        # Initialize questions
        questions = await self._get_quiz_questions(quiz)
        question_ids = [q.id for q in questions]
        
        session.question_ids = question_ids
        session.current_question_index = 0
        session.status = QuizSessionStatus.IN_PROGRESS
        session.started_at = datetime.now(timezone.utc)
        session.last_activity_at = datetime.now(timezone.utc)
        session.time_limit_minutes = quiz.time_limit_minutes
        
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def get_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """Get a session by ID."""
        result = await self.db.execute(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_session(
        self,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        include_completed: bool = False,
    ) -> QuizSession | None:
        """Get user's active session for a quiz."""
        query = select(QuizSession).where(
            QuizSession.user_id == user_id,
            QuizSession.quiz_id == quiz_id,
        )
        
        if not include_completed:
            query = query.where(
                QuizSession.status.in_([
                    QuizSessionStatus.NOT_STARTED,
                    QuizSessionStatus.IN_PROGRESS,
                    QuizSessionStatus.PAUSED,
                ])
            )
        
        query = query.order_by(QuizSession.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def pause_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """Pause a quiz session."""
        session = await self.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            return None
        
        session.status = QuizSessionStatus.PAUSED
        await self._update_time_spent(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def resume_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """Resume a paused session."""
        session = await self.get_session(session_id)
        if not session or session.status != QuizSessionStatus.PAUSED:
            return None
        
        session.status = QuizSessionStatus.IN_PROGRESS
        session.last_activity_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def complete_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """Complete a quiz session."""
        session = await self.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            return None
        
        session.status = QuizSessionStatus.COMPLETED
        session.completed_at = datetime.now(timezone.utc)
        await self._update_time_spent(session)
        await self._calculate_score(session)
        
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def abandon_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """Mark a session as abandoned."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.status = QuizSessionStatus.ABANDONED
        session.completed_at = datetime.now(timezone.utc)
        await self._update_time_spent(session)
        
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def expire_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """Mark a session as expired (time limit reached)."""
        session = await self.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            return None
        
        session.status = QuizSessionStatus.EXPIRED
        session.completed_at = datetime.now(timezone.utc)
        await self._update_time_spent(session)
        await self._calculate_score(session)
        
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def update_ability(
        self,
        session_id: uuid.UUID,
        ability: float,
        ability_std: float,
    ) -> None:
        """Update session ability estimate."""
        session = await self.get_session(session_id)
        if not session:
            return
        
        session.estimated_ability = ability
        session.ability_std = ability_std
        await self.db.flush()
    
    async def update_current_question(self, session_id: uuid.UUID, index: int) -> None:
        """Update current question index."""
        session = await self.get_session(session_id)
        if not session:
            return
        
        session.current_question_index = index
        session.last_activity_at = datetime.now(timezone.utc)
        await self.db.flush()
    
    async def list_user_sessions(
        self,
        user_id: uuid.UUID,
        status: QuizSessionStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[QuizSession], int]:
        """List user's quiz sessions."""
        query = select(QuizSession).where(QuizSession.user_id == user_id)
        count_query = select(func.count(QuizSession.id)).where(
            QuizSession.user_id == user_id
        )
        
        if status:
            query = query.where(QuizSession.status == status)
            count_query = count_query.where(QuizSession.status == status)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.order_by(QuizSession.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        return sessions, total
    
    async def get_current_question(
        self,
        session_id: uuid.UUID,
    ) -> tuple[Question | None, int]:
        """Get current question and its index."""
        session = await self.get_session(session_id)
        if not session:
            return None, -1
        
        if session.current_question_index >= len(session.question_ids):
            return None, -1
        
        question_id = session.question_ids[session.current_question_index]
        result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        return question, session.current_question_index
    
    async def _get_quiz(self, quiz_id: uuid.UUID) -> Quiz | None:
        """Get quiz by ID."""
        result = await self.db.execute(
            select(Quiz).where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_quiz_questions(self, quiz: Quiz) -> list[Question]:
        """Get questions for a quiz."""
        if not quiz.question_ids:
            result = await self.db.execute(
                select(Question)
                .where(Question.quiz_id == quiz.id)
                .where(Question.is_active == True)
            )
        else:
            result = await self.db.execute(
                select(Question).where(Question.id.in_(quiz.question_ids))
            )
        
        questions = list(result.scalars().all())
        
        # Shuffle if needed
        if quiz.shuffle_questions:
            import random
            random.shuffle(questions)
        
        return questions
    
    async def _update_time_spent(self, session: QuizSession) -> None:
        """Update time spent on session."""
        if session.started_at and session.last_activity_at:
            delta = session.last_activity_at - session.started_at
            session.time_spent_seconds = int(delta.total_seconds())
    
    async def _calculate_score(self, session: QuizSession) -> None:
        """Calculate session score."""
        from src.models import QuestionResponse
        
        result = await self.db.execute(
            select(QuestionResponse)
            .where(QuestionResponse.session_id == session.id)
        )
        responses = list(result.scalars().all())
        
        if not responses:
            return
        
        # Calculate raw score
        correct_count = sum(1 for r in responses if r.is_correct)
        total_count = len(responses)
        
        session.raw_score = correct_count
        
        # Calculate percentage
        if total_count > 0:
            session.percentage_score = (correct_count / total_count) * 100
        
        # Check pass/fail
        quiz = await self._get_quiz(session.quiz_id)
        if quiz:
            session.passed = session.percentage_score >= quiz.passing_score if session.percentage_score else False
