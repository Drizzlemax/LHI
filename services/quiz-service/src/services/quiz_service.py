"""
PANDORA Quiz Service Quiz Management Service
"""
import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Quiz, QuizStatus, Question
from src.schemas.quiz import QuizCreate, QuizUpdate


class QuizService:
    """Service for quiz management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_quiz(self, quiz_data: QuizCreate) -> Quiz:
        """Create a new quiz."""
        quiz = Quiz(
            title=quiz_data.title,
            description=quiz_data.description,
            question_ids=quiz_data.question_ids,
            question_type=quiz_data.question_type,
            time_limit_minutes=quiz_data.time_limit_minutes,
            allowed_attempts=quiz_data.allowed_attempts,
            cooldown_minutes=quiz_data.cooldown_minutes,
            passing_score=quiz_data.passing_score,
            max_score=quiz_data.max_score,
            points_per_question=quiz_data.points_per_question,
            is_adaptive=quiz_data.is_adaptive,
            shuffle_questions=quiz_data.shuffle_questions,
            shuffle_answers=quiz_data.shuffle_answers,
            show_correct_answers=quiz_data.show_correct_answers,
            show_explanations=quiz_data.show_explanations,
            allow_back_navigation=quiz_data.allow_back_navigation,
            learning_path_id=quiz_data.learning_path_id,
            module_id=quiz_data.module_id,
            difficulty_level=quiz_data.difficulty_level,
            status=QuizStatus.DRAFT,
        )
        self.db.add(quiz)
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def get_quiz(self, quiz_id: uuid.UUID) -> Quiz | None:
        """Get a quiz by ID."""
        result = await self.db.execute(
            select(Quiz).where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()
    
    async def update_quiz(self, quiz_id: uuid.UUID, quiz_data: QuizUpdate) -> Quiz | None:
        """Update a quiz."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return None
        
        update_data = quiz_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(quiz, key, value)
        
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def delete_quiz(self, quiz_id: uuid.UUID, soft: bool = True) -> bool:
        """Delete a quiz."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return False
        
        if soft:
            quiz.status = QuizStatus.DELETED
        else:
            await self.db.delete(quiz)
        
        await self.db.flush()
        return True
    
    async def publish_quiz(self, quiz_id: uuid.UUID) -> Quiz | None:
        """Publish a quiz."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return None
        
        quiz.status = QuizStatus.PUBLISHED
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def archive_quiz(self, quiz_id: uuid.UUID) -> Quiz | None:
        """Archive a quiz."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return None
        
        quiz.status = QuizStatus.ARCHIVED
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def list_quizzes(
        self,
        status: QuizStatus | None = None,
        learning_path_id: uuid.UUID | None = None,
        module_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Quiz], int]:
        """List quizzes with filters."""
        query = select(Quiz)
        count_query = select(func.count(Quiz.id))
        
        if status:
            query = query.where(Quiz.status == status)
            count_query = count_query.where(Quiz.status == status)
        
        if learning_path_id:
            query = query.where(Quiz.learning_path_id == learning_path_id)
            count_query = count_query.where(Quiz.learning_path_id == learning_path_id)
        
        if module_id:
            query = query.where(Quiz.module_id == module_id)
            count_query = count_query.where(Quiz.module_id == module_id)
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        quizzes = result.scalars().all()
        
        return quizzes, total
    
    async def add_questions(self, quiz_id: uuid.UUID, question_ids: list[uuid.UUID]) -> Quiz | None:
        """Add questions to a quiz."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return None
        
        current_ids = quiz.question_ids or []
        quiz.question_ids = list(set(current_ids + question_ids))
        
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def remove_questions(self, quiz_id: uuid.UUID, question_ids: list[uuid.UUID]) -> Quiz | None:
        """Remove questions from a quiz."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return None
        
        current_ids = quiz.question_ids or []
        quiz.question_ids = [qid for qid in current_ids if qid not in question_ids]
        
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def get_quiz_questions(self, quiz_id: uuid.UUID) -> list[Question]:
        """Get all questions for a quiz."""
        result = await self.db.execute(
            select(Question)
            .where(Question.quiz_id == quiz_id)
            .where(Question.is_active == True)
            .order_by(Question.created_at)
        )
        return list(result.scalars().all())
    
    async def update_statistics(self, quiz_id: uuid.UUID) -> None:
        """Update quiz statistics."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return
        
        # Get session statistics
        from src.models import QuizSession, QuizSessionStatus
        
        result = await self.db.execute(
            select(
                func.count(QuizSession.id).label("total_attempts"),
                func.avg(QuizSession.percentage_score).label("avg_score"),
                func.count(
                    func.nullif(
                        QuizSession.percentage_score < quiz.passing_score, True
                    )
                ).label("completed"),
            )
            .where(QuizSession.quiz_id == quiz_id)
            .where(QuizSession.status == QuizSessionStatus.COMPLETED)
        )
        row = result.one()
        
        quiz.total_attempts = row.total_attempts or 0
        quiz.average_score = float(row.avg_score) if row.avg_score else None
        
        await self.db.flush()
