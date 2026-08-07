"""Initial learning path models

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create learning_paths table
    op.create_table(
        'learning_paths',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', 'DELETED', name='learning_path_status'), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('is_enrolled', sa.Boolean(), nullable=False),
        sa.Column('allow_early_access', sa.Boolean(), nullable=False),
        sa.Column('target_education_level', sa.String(length=50), nullable=True),
        sa.Column('difficulty_level', sa.String(length=20), nullable=True),
        sa.Column('module_count', sa.Integer(), nullable=False),
        sa.Column('lesson_count', sa.Integer(), nullable=False),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('enrollment_count', sa.Integer(), nullable=False),
        sa.Column('completion_count', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_paths_id', 'learning_paths', ['id'])
    op.create_index('ix_learning_paths_user_id', 'learning_paths', ['user_id'])
    op.create_index('ix_learning_paths_course_id', 'learning_paths', ['course_id'])
    op.create_index('ix_learning_paths_status', 'learning_paths', ['status'])
    op.create_index('ix_learning_paths_target_education_level', 'learning_paths', ['target_education_level'])
    op.create_index('ix_learning_paths_status_created', 'learning_paths', ['status', 'created_at'])
    op.create_index('ix_learning_paths_user_status', 'learning_paths', ['user_id', 'status'])
    op.create_index('ix_learning_paths_target_level_status', 'learning_paths', ['target_education_level', 'status'])
    op.create_unique_constraint('uq_learning_paths_user_course', 'learning_paths', ['user_id', 'course_id'])

    # Create modules table
    op.create_table(
        'modules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('learning_path_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('LOCKED', 'AVAILABLE', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED', name='module_status'), nullable=False),
        sa.Column('lesson_count', sa.Integer(), nullable=False),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('prerequisite_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('is_optional', sa.Boolean(), nullable=False),
        sa.Column('is_bonus', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_modules_id', 'modules', ['id'])
    op.create_index('ix_modules_learning_path_id', 'modules', ['learning_path_id'])
    op.create_index('ix_modules_status', 'modules', ['status'])
    op.create_index('ix_modules_path_order', 'modules', ['learning_path_id', 'order_index'])
    op.create_unique_constraint('uq_modules_path_order', 'modules', ['learning_path_id', 'order_index'])

    # Create path_lessons table
    op.create_table(
        'path_lessons',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('lesson_type', sa.Enum('VIDEO', 'ARTICLE', 'QUIZ', 'ASSIGNMENT', 'PROJECT', 'LIVE_SESSION', 'INTERACTIVE', 'EXAM', name='lesson_type'), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('LOCKED', 'AVAILABLE', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED', name='lesson_status'), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('xp_reward', sa.Integer(), nullable=False),
        sa.Column('prerequisite_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('content_config', postgresql.JSON(), nullable=True),
        sa.Column('completion_requirements', postgresql.JSON(), nullable=True),
        sa.Column('is_optional', sa.Boolean(), nullable=False),
        sa.Column('is_preview', sa.Boolean(), nullable=False),
        sa.Column('is_bonus', sa.Boolean(), nullable=False),
        sa.Column('allow_replay', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_path_lessons_id', 'path_lessons', ['id'])
    op.create_index('ix_path_lessons_module_id', 'path_lessons', ['module_id'])
    op.create_index('ix_path_lessons_content_id', 'path_lessons', ['content_id'])
    op.create_index('ix_path_lessons_lesson_type', 'path_lessons', ['lesson_type'])
    op.create_index('ix_path_lessons_status', 'path_lessons', ['status'])
    op.create_index('ix_path_lessons_module_order', 'path_lessons', ['module_id', 'order_index'])
    op.create_unique_constraint('uq_path_lessons_module_order', 'path_lessons', ['module_id', 'order_index'])

    # Create user_progress table
    op.create_table(
        'user_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lesson_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('learning_path_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED', name='progress_status'), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
        sa.Column('last_position_seconds', sa.Integer(), nullable=True),
        sa.Column('quiz_results', postgresql.JSON(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('points_earned', sa.Integer(), nullable=False),
        sa.Column('completion_note', sa.Text(), nullable=True),
        sa.Column('completion_method', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['path_lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_progress_id', 'user_progress', ['id'])
    op.create_index('ix_user_progress_user_id', 'user_progress', ['user_id'])
    op.create_index('ix_user_progress_lesson_id', 'user_progress', ['lesson_id'])
    op.create_index('ix_user_progress_learning_path_id', 'user_progress', ['learning_path_id'])
    op.create_index('ix_user_progress_module_id', 'user_progress', ['module_id'])
    op.create_index('ix_user_progress_status', 'user_progress', ['status'])
    op.create_index('ix_user_progress_user_lesson', 'user_progress', ['user_id', 'lesson_id'])
    op.create_index('ix_user_progress_user_path', 'user_progress', ['user_id', 'learning_path_id'])
    op.create_index('ix_user_progress_user_module', 'user_progress', ['user_id', 'module_id'])
    op.create_unique_constraint('uq_user_progress_user_lesson', 'user_progress', ['user_id', 'lesson_id'])

    # Create user_learning_stats table
    op.create_table(
        'user_learning_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lessons_completed', sa.Integer(), nullable=False),
        sa.Column('quizzes_passed', sa.Integer(), nullable=False),
        sa.Column('quizzes_failed', sa.Integer(), nullable=False),
        sa.Column('paths_enrolled', sa.Integer(), nullable=False),
        sa.Column('paths_completed', sa.Integer(), nullable=False),
        sa.Column('total_time_seconds', sa.Integer(), nullable=False),
        sa.Column('total_xp', sa.Integer(), nullable=False),
        sa.Column('current_streak_days', sa.Integer(), nullable=False),
        sa.Column('longest_streak_days', sa.Integer(), nullable=False),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('highest_score', sa.Float(), nullable=True),
        sa.Column('badges', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('achievements', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_learning_stats_id', 'user_learning_stats', ['id'])
    op.create_index('ix_user_learning_stats_user_id', 'user_learning_stats', ['user_id'])
    op.create_unique_constraint('uq_user_learning_stats_user_id', 'user_learning_stats', ['user_id'])

    # Create learning_path_enrollments table
    op.create_table(
        'learning_path_enrollments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('learning_path_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enrolled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('enrollment_source', sa.String(length=50), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('current_module_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_lesson_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('completion_percentage', sa.Float(), nullable=True),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unenrolled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_path_enrollments_id', 'learning_path_enrollments', ['id'])
    op.create_index('ix_learning_path_enrollments_user_id', 'learning_path_enrollments', ['user_id'])
    op.create_index('ix_learning_path_enrollments_learning_path_id', 'learning_path_enrollments', ['learning_path_id'])
    op.create_index('ix_learning_path_enrollments_user_path', 'learning_path_enrollments', ['user_id', 'learning_path_id'])
    op.create_index('ix_learning_path_enrollments_path_active', 'learning_path_enrollments', ['learning_path_id', 'is_active'])
    op.create_unique_constraint('uq_enrollments_user_path', 'learning_path_enrollments', ['user_id', 'learning_path_id'])


def downgrade() -> None:
    op.drop_table('learning_path_enrollments')
    op.drop_table('user_learning_stats')
    op.drop_table('user_progress')
    op.drop_table('path_lessons')
    op.drop_table('modules')
    op.drop_table('learning_paths')
