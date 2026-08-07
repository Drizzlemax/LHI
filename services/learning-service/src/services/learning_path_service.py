"""
PANDORA Learning Service - Learning Path Service
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import (
    LearningPath,
    Module,
    PathLesson,
    UserProgress,
    LearningPathEnrollment,
    LearningPathStatus,
    ModuleStatus,
    LessonStatus,
    ProgressStatus,
)
from src.schemas.learning_path import (
    LearningPathCreate,
    LearningPathUpdate,
    LearningPathProgress,
    ModuleProgress,
    LessonProgress,
    ProgressUpdate,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


class LearningPathService:
    """Service for managing learning paths."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def create_learning_path(
        self,
        data: LearningPathCreate,
        user_id: uuid.UUID | None = None,
    ) -> LearningPath:
        """Create a new learning path with modules."""
        path = LearningPath(
            user_id=user_id,
            title=data.title,
            description=data.description,
            goal=data.goal,
            target_education_level=data.target_education_level,
            difficulty_level=data.difficulty_level,
            is_public=data.is_public,
            status=LearningPathStatus.DRAFT,
            progress_percentage=0.0,
        )

        self.db.add(path)
        await self.db.flush()

        # Create modules
        total_lessons = 0
        for module_data in data.modules:
            module = Module(
                learning_path_id=path.id,
                title=module_data.title,
                description=module_data.description,
                order_index=module_data.order_index,
                estimated_hours=module_data.estimated_hours,
                is_optional=module_data.is_optional,
                is_bonus=module_data.is_bonus,
                status=ModuleStatus.LOCKED,
                lesson_count=0,
            )
            self.db.add(module)
            await self.db.flush()

        # Update counts
        path.module_count = len(data.modules)
        path.lesson_count = total_lessons

        await self.db.commit()
        await self.db.refresh(path)

        logger.info("learning_path_created", path_id=str(path.id))
        return path

    async def get_learning_path(
        self,
        path_id: uuid.UUID,
        include_modules: bool = True,
    ) -> LearningPath | None:
        """Get a learning path by ID."""
        query = select(LearningPath).where(LearningPath.id == path_id)

        if include_modules:
            query = query.options(
                selectinload(LearningPath.modules).selectinload(Module.lessons)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_learning_path_by_user(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
        include_modules: bool = True,
    ) -> LearningPath | None:
        """Get a learning path by ID and user."""
        query = select(LearningPath).where(
            and_(
                LearningPath.id == path_id,
                LearningPath.user_id == user_id,
            )
        )

        if include_modules:
            query = query.options(
                selectinload(LearningPath.modules).selectinload(Module.lessons)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_learning_paths(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: uuid.UUID | None = None,
        status: LearningPathStatus | None = None,
        target_education_level: str | None = None,
        include_public: bool = True,
    ) -> tuple[Sequence[LearningPath], int]:
        """List learning paths with filters."""
        query = select(LearningPath)

        conditions = []
        if user_id:
            conditions.append(LearningPath.user_id == user_id)
        if status:
            conditions.append(LearningPath.status == status)
        if target_education_level:
            conditions.append(
                LearningPath.target_education_level == target_education_level
            )
        if not include_public:
            conditions.append(LearningPath.is_public == False)
        else:
            conditions.append(
                (LearningPath.is_public == True) | (LearningPath.user_id == user_id)
            )

        # Exclude deleted
        conditions.append(LearningPath.status != LearningPathStatus.DELETED)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)
        query = query.order_by(LearningPath.created_at.desc())

        result = await self.db.execute(query)
        paths = result.scalars().all()

        return paths, total

    async def update_learning_path(
        self,
        path_id: uuid.UUID,
        data: LearningPathUpdate,
    ) -> LearningPath | None:
        """Update a learning path."""
        path = await self.get_learning_path(path_id)
        if not path:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(path, field, value)

        path.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(path)

        logger.info("learning_path_updated", path_id=str(path_id))
        return path

    async def delete_learning_path(
        self,
        path_id: uuid.UUID,
    ) -> bool:
        """Soft delete a learning path."""
        path = await self.get_learning_path(path_id)
        if not path:
            return False

        path.status = LearningPathStatus.DELETED
        path.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

        logger.info("learning_path_deleted", path_id=str(path_id))
        return True

    async def publish_learning_path(
        self,
        path_id: uuid.UUID,
    ) -> LearningPath | None:
        """Publish a learning path."""
        path = await self.get_learning_path(path_id)
        if not path:
            return None

        path.status = LearningPathStatus.PUBLISHED
        path.published_at = datetime.now(timezone.utc)
        path.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(path)

        logger.info("learning_path_published", path_id=str(path_id))
        return path

    # ============ Enrollment ============

    async def enroll_in_learning_path(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> LearningPathEnrollment:
        """Enroll user in a learning path."""
        # Check if already enrolled
        query = select(LearningPathEnrollment).where(
            and_(
                LearningPathEnrollment.user_id == user_id,
                LearningPathEnrollment.learning_path_id == path_id,
            )
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_active = True
            existing.unenrolled_at = None
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Create enrollment
        enrollment = LearningPathEnrollment(
            user_id=user_id,
            learning_path_id=path_id,
            progress_percentage=0.0,
        )
        self.db.add(enrollment)

        # Update path enrollment count
        path = await self.get_learning_path(path_id)
        if path:
            path.enrollment_count += 1

        await self.db.commit()
        await self.db.refresh(enrollment)

        logger.info("user_enrolled", user_id=str(user_id), path_id=str(path_id))
        return enrollment

    async def unenroll_from_learning_path(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Unenroll user from a learning path."""
        query = select(LearningPathEnrollment).where(
            and_(
                LearningPathEnrollment.user_id == user_id,
                LearningPathEnrollment.learning_path_id == path_id,
            )
        )
        result = await self.db.execute(query)
        enrollment = result.scalar_one_or_none()

        if not enrollment:
            return False

        enrollment.is_active = False
        enrollment.unenrolled_at = datetime.now(timezone.utc)
        await self.db.commit()

        logger.info("user_unenrolled", user_id=str(user_id), path_id=str(path_id))
        return True

    # ============ Progress ============

    async def get_path_progress(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> LearningPathProgress | None:
        """Get user's progress in a learning path."""
        path = await self.get_learning_path(path_id)
        if not path:
            return None

        # Get all progress for this user and path
        query = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.learning_path_id == path_id,
            )
        )
        result = await self.db.execute(query)
        progress_records = result.scalars().all()

        # Build progress map
        progress_map = {str(p.lesson_id): p for p in progress_records}

        # Build module progress
        modules_progress = []
        total_lessons = 0
        completed_lessons = 0

        for module in path.modules:
            module_progress_map = {str(l.id): progress_map.get(str(l.id)) for l in module.lessons}
            total_lessons += len(module.lessons)

            lessons_progress = []
            module_completed = 0

            for lesson in module.lessons:
                lp = module_progress_map.get(str(lesson.id))
                total_lessons += 1

                if lp and lp.status == ProgressStatus.COMPLETED:
                    completed_lessons += 1
                    module_completed += 1

                lessons_progress.append(LessonProgress(
                    lesson_id=lesson.id,
                    title=lesson.title,
                    lesson_type=lesson.lesson_type.value if hasattr(lesson.lesson_type, 'value') else str(lesson.lesson_type),
                    status=lp.status.value if lp else ProgressStatus.NOT_STARTED.value,
                    progress_percentage=lp.progress_percentage if lp else 0.0,
                    score=lp.score,
                    time_spent_seconds=lp.time_spent_seconds if lp else 0,
                    started_at=lp.started_at if lp else None,
                    completed_at=lp.completed_at if lp else None,
                ))

            # Calculate module progress
            module_pct = (module_completed / len(module.lessons) * 100) if module.lessons else 0

            modules_progress.append(ModuleProgress(
                module_id=module.id,
                title=module.title,
                status=module.status.value if hasattr(module.status, 'value') else str(module.status),
                progress_percentage=module_pct,
                lessons=lessons_progress,
                completed_lessons=module_completed,
                total_lessons=len(module.lessons),
            ))

        # Calculate overall progress
        overall_pct = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

        return LearningPathProgress(
            learning_path_id=path_id,
            title=path.title,
            status=path.status.value if hasattr(path.status, 'value') else str(path.status),
            progress_percentage=overall_pct,
            modules=modules_progress,
            completed_modules=sum(1 for m in modules_progress if m.completed_lessons == m.total_lessons),
            total_modules=len(modules_progress),
            completed_lessons=completed_lessons,
            total_lessons=total_lessons,
            total_time_spent_seconds=sum(
                p.time_spent_seconds for p in progress_records if p
            ),
        )

    async def update_lesson_progress(
        self,
        path_id: uuid.UUID,
        lesson_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ProgressUpdate,
    ) -> UserProgress | None:
        """Update user's progress for a lesson."""
        # Find or create progress record
        query = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id,
            )
        )
        result = await self.db.execute(query)
        progress = result.scalar_one_or_none()

        if not progress:
            # Create new progress record
            progress = UserProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                learning_path_id=path_id,
                status=ProgressStatus.NOT_STARTED,
                progress_percentage=0.0,
                time_spent_seconds=0,
            )
            self.db.add(progress)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value:
                progress.status = ProgressStatus(value)
                if progress.status == ProgressStatus.IN_PROGRESS and not progress.started_at:
                    progress.started_at = datetime.now(timezone.utc)
                elif progress.status == ProgressStatus.COMPLETED:
                    progress.completed_at = datetime.now(timezone.utc)
                    progress.progress_percentage = 100.0
            elif field == "quiz_results":
                progress.quiz_results = value
            else:
                setattr(progress, field, value)

        progress.updated_at = datetime.now(timezone.utc)
        progress.last_accessed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(progress)

        # Update module progress
        await self._update_module_progress(path_id, user_id)

        logger.info(
            "lesson_progress_updated",
            user_id=str(user_id),
            lesson_id=str(lesson_id),
            status=progress.status.value if hasattr(progress.status, 'value') else str(progress.status),
        )
        return progress

    async def _update_module_progress(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Update module progress based on lesson progress."""
        path = await self.get_learning_path(path_id, include_modules=True)
        if not path:
            return

        for module in path.modules:
            # Get progress for all lessons in module
            lesson_ids = [l.id for l in module.lessons]
            if not lesson_ids:
                continue

            query = select(UserProgress).where(
                and_(
                    UserProgress.user_id == user_id,
                    UserProgress.lesson_id.in_(lesson_ids),
                )
            )
            result = await self.db.execute(query)
            lesson_progress = result.scalars().all()

            completed = sum(
                1 for p in lesson_progress
                if p.status == ProgressStatus.COMPLETED
            )

            module.lesson_count = len(module.lessons)
            module.progress_percentage = (completed / len(module.lessons) * 100) if module.lessons else 0

            if completed == len(module.lessons):
                module.status = ModuleStatus.COMPLETED
                module.completed_at = datetime.now(timezone.utc)
            elif completed > 0:
                module.status = ModuleStatus.IN_PROGRESS

        await self.db.commit()
