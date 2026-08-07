"""
PANDORA Quiz Service Response Management Service
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import QuestionResponse, Question, QuizSession


class ResponseService:
    """Service for managing question responses."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_response(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        sequence_number: int,
        ability_at_time: float = 0.0,
    ) -> QuestionResponse:
        """Create a new response record."""
        response = QuestionResponse(
            session_id=session_id,
            question_id=question_id,
            sequence_number=sequence_number,
            ability_at_time=ability_at_time,
            question_started_at=datetime.now(timezone.utc),
        )
        self.db.add(response)
        await self.db.flush()
        await self.db.refresh(response)
        return response
    
    async def submit_response(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        user_answer: dict,
        time_spent_seconds: int = 0,
    ) -> QuestionResponse | None:
        """Submit a response to a question."""
        response = await self.get_response(session_id, question_id)
        
        if not response:
            return None
        
        response.user_answer = user_answer
        response.time_spent_seconds = time_spent_seconds
        response.answered_at = datetime.now(timezone.utc)
        
        # Check correctness
        question = await self._get_question(question_id)
        if question and question.correct_answer:
            is_correct = self._check_answer(user_answer, question.correct_answer)
            response.is_correct = is_correct
            response.partial_score = float(is_correct) * response.sequence_number
        
        await self.db.flush()
        await self.db.refresh(response)
        return response
    
    async def get_response(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> QuestionResponse | None:
        """Get a specific response."""
        result = await self.db.execute(
            select(QuestionResponse).where(
                QuestionResponse.session_id == session_id,
                QuestionResponse.question_id == question_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_session_responses(self, session_id: uuid.UUID) -> list[QuestionResponse]:
        """Get all responses for a session."""
        result = await self.db.execute(
            select(QuestionResponse)
            .where(QuestionResponse.session_id == session_id)
            .order_by(QuestionResponse.sequence_number)
        )
        return list(result.scalars().all())
    
    async def update_flag(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        is_flagged: bool,
    ) -> QuestionResponse | None:
        """Update flag status for a question."""
        response = await self.get_response(session_id, question_id)
        if not response:
            return None
        
        response.is_flagged = is_flagged
        await self.db.flush()
        await self.db.refresh(response)
        return response
    
    async def mark_skipped(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> QuestionResponse | None:
        """Mark a question as skipped."""
        response = await self.get_response(session_id, question_id)
        if not response:
            return None
        
        response.is_skipped = True
        await self.db.flush()
        await self.db.refresh(response)
        return response
    
    async def update_difficulty_at_time(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        difficulty: float,
    ) -> None:
        """Update the difficulty parameter at time of response."""
        response = await self.get_response(session_id, question_id)
        if response:
            response.difficulty_at_time = difficulty
            await self.db.flush()
    
    async def show_explanation(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> Question | None:
        """Mark explanation as shown and return the question."""
        response = await self.get_response(session_id, question_id)
        if response:
            response.explanation_shown = True
            await self.db.flush()
        
        return await self._get_question(question_id)
    
    async def get_answer_for_review(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> tuple[QuestionResponse | None, Question | None]:
        """Get response and question for review."""
        response = await self.get_response(session_id, question_id)
        question = await self._get_question(question_id)
        return response, question
    
    async def _get_question(self, question_id: uuid.UUID) -> Question | None:
        """Get question by ID."""
        result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one_or_none()
    
    def _check_answer(self, user_answer: dict, correct_answer: dict) -> bool:
        """Check if user's answer matches correct answer."""
        if not user_answer or not correct_answer:
            return False
        
        answer_type = correct_answer.get("type", "single")
        
        if answer_type == "single":
            return user_answer.get("value") == correct_answer.get("value")
        
        elif answer_type == "multiple":
            user_values = set(user_answer.get("values", []))
            correct_values = set(correct_answer.get("values", []))
            return user_values == correct_values
        
        elif answer_type == "text":
            # Case-insensitive comparison for text answers
            user_text = user_answer.get("value", "").strip().lower()
            correct_text = correct_answer.get("value", "").strip().lower()
            return user_text == correct_text
        
        return False
