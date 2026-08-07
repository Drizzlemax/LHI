"""
PANDORA Quiz Service Adaptive Testing Engine
"""
import uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.irt.estimator import IRTEstimator
from src.irt.item_selector import ItemSelector
from src.irt.models import AbilityEstimate, ItemParameters, ResponsePattern
from src.models import Question, QuestionResponse, QuizSession
from src.models import QuizSessionStatus


class AdaptiveEngine:
    """Engine for adaptive quiz delivery using IRT."""
    
    def __init__(
        self,
        db: AsyncSession,
        model: Literal["2pl", "3pl"] = "3pl",
        selection_method: Literal["maximum_information", "minimum_error", "random"] = "maximum_information",
        max_items: int = 50,
        convergence_threshold: float = 0.3,
        randomization: float = 0.1,
    ):
        self.db = db
        self.estimator = IRTEstimator(model=model)
        self.selector = ItemSelector(
            model=model,
            selection_method=selection_method,
            randomization=randomization,
        )
        self.max_items = max_items
        self.convergence_threshold = convergence_threshold
    
    async def select_next_question(
        self,
        session: QuizSession,
    ) -> tuple[Question | None, AbilityEstimate]:
        """Select the next question for adaptive testing.
        
        Returns:
            Tuple of (selected question, current ability estimate)
        """
        # Get current ability estimate
        ability = AbilityEstimate(
            theta=session.estimated_ability,
            standard_error=session.ability_std,
            information=1.0 / (session.ability_std ** 2) if session.ability_std > 0 else 1.0,
        )
        
        # Get answered questions
        answered = set(session.answered_questions or [])
        available_items = await self._get_available_items(session.quiz_id, answered)
        
        if not available_items:
            return None, ability
        
        # Convert to IRT parameters
        item_params = [
            ItemParameters(
                item_id=str(item.id),
                difficulty=item.difficulty,
                discrimination=item.discrimination,
                guessing=item.guessing_parameter,
            )
            for item in available_items
        ]
        
        # Select next item
        selection_info = self.selector.select_next_item(
            current_ability=ability,
            available_items=item_params,
            used_item_ids=answered,
        )
        
        if not selection_info:
            return None, ability
        
        # Find the question
        selected_question = next(
            (q for q in available_items if str(q.id) == selection_info.item_id),
            None,
        )
        
        return selected_question, ability
    
    async def process_response(
        self,
        session: QuizSession,
        question: Question,
        user_answer: dict,
        is_correct: bool,
    ) -> AbilityEstimate:
        """Process a response and update ability estimate.
        
        Returns:
            Updated ability estimate
        """
        # Get all responses for this session
        responses = await self._get_session_responses(session.id)
        
        # Build response pattern
        item_params: list[ItemParameters] = []
        response_list: list[bool] = []
        used_ids: list[str] = []
        
        for resp in responses:
            if resp.question_id == question.id:
                # Add the new response
                item_params.append(
                    ItemParameters(
                        item_id=str(question.id),
                        difficulty=question.difficulty,
                        discrimination=question.discrimination,
                        guessing=question.guessing_parameter,
                    )
                )
                response_list.append(is_correct)
                used_ids.append(str(question.id))
            else:
                # Add existing response
                q = await self._get_question(resp.question_id)
                if q:
                    item_params.append(
                        ItemParameters(
                            item_id=str(q.id),
                            difficulty=q.difficulty,
                            discrimination=q.discrimination,
                            guessing=q.guessing_parameter,
                        )
                    )
                    response_list.append(resp.is_correct or False)
                    used_ids.append(str(q.id))
        
        # Estimate ability
        pattern = ResponsePattern(
            item_ids=used_ids,
            responses=response_list,
        )
        
        ability = self.estimator.estimate_ability(pattern, item_params)
        
        # Update session
        session.estimated_ability = ability.theta
        session.ability_std = ability.standard_error
        
        # Add to response history
        history = session.response_history or []
        history.append({
            "question_id": str(question.id),
            "is_correct": is_correct,
            "ability_before": session.estimated_ability,
            "ability_after": ability.theta,
        })
        session.response_history = history
        
        await self.db.flush()
        
        return ability
    
    async def check_termination(
        self,
        session: QuizSession,
        ability: AbilityEstimate,
    ) -> tuple[bool, str]:
        """Check if adaptive testing should terminate.
        
        Returns:
            Tuple of (should_terminate, reason)
        """
        answered_count = len(session.answered_questions or [])
        
        # Check maximum items
        if answered_count >= self.max_items:
            return True, "maximum_items_reached"
        
        # Check convergence
        if ability.standard_error < self.convergence_threshold:
            return True, "convergence_achieved"
        
        # Check if no more items available
        available_items = await self._get_available_items(
            session.quiz_id,
            set(session.answered_questions or []),
        )
        if not available_items:
            return True, "no_more_items"
        
        return False, ""
    
    async def calculate_final_score(
        self,
        session: QuizSession,
        ability: AbilityEstimate,
    ) -> dict:
        """Calculate final score based on ability estimate.
        
        Returns:
            Dictionary with score information
        """
        # Get all responses
        responses = await self._get_session_responses(session.id)
        correct_count = sum(1 for r in responses if r.is_correct)
        total_count = len(responses)
        
        # Percentage score
        percentage = (correct_count / total_count * 100) if total_count > 0 else 0.0
        
        # Scaled score (using ability)
        scaled_score = self._ability_to_score(ability.theta)
        
        return {
            "raw_score": correct_count,
            "total_questions": total_count,
            "percentage_score": percentage,
            "scaled_score": scaled_score,
            "estimated_ability": ability.theta,
            "standard_error": ability.standard_error,
            "information": ability.information,
        }
    
    def _ability_to_score(self, theta: float, scale: float = 25) -> float:
        """Convert ability estimate to a 0-100 scale.
        
        Args:
            theta: Ability estimate
            scale: Scale factor (higher = more spread)
        
        Returns:
            Score from 0 to 100
        """
        # Typical conversion: 50 + 10 * theta
        # Using sigmoid-like transformation
        score = 100 / (1 + 2 ** (-theta * scale / 10))
        return max(0.0, min(100.0, score))
    
    async def _get_available_items(
        self,
        quiz_id: uuid.UUID,
        exclude_ids: set,
    ) -> list[Question]:
        """Get available questions for a quiz."""
        query = select(Question).where(
            Question.quiz_id == quiz_id,
            Question.is_active == True,
        )
        
        if exclude_ids:
            query = query.where(Question.id.not_in(exclude_ids))
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _get_session_responses(self, session_id: uuid.UUID) -> list[QuestionResponse]:
        """Get all responses for a session."""
        result = await self.db.execute(
            select(QuestionResponse)
            .where(QuestionResponse.session_id == session_id)
            .order_by(QuestionResponse.sequence_number)
        )
        return list(result.scalars().all())
    
    async def _get_question(self, question_id: uuid.UUID) -> Question | None:
        """Get a question by ID."""
        result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one_or_none()
