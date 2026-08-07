"""Initial assessment models

Revision ID: 000001
Revises: 
Create Date: 2025-08-05

This migration creates the assessment-related tables:
- assessments: Main assessment/exam table
- assessment_questions: Questions within assessments
- assessment_attempts: User attempts at assessments
- answers: User answers to assessment questions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assessments table
    op.create_table(
        'assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assessment_type', sa.String(20), nullable=False, server_default='quiz'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('allowed_attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True),
        sa.Column('passing_score', sa.Float(), nullable=False, server_default='60.0'),
        sa.Column('max_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('grading_type', sa.String(20), nullable=False, server_default='automatic'),
        sa.Column('show_correct_answers', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_explanations', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_score_immediately', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('shuffle_questions', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shuffle_answers', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allow_back_navigation', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_skip', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('available_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('available_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('learning_path_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('difficulty_level', sa.String(20), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('pass_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for assessments
    op.create_index('ix_assessments_status_created', 'assessments', ['status', 'created_at'])
    op.create_index('ix_assessments_content', 'assessments', ['content_id'])
    op.create_index('ix_assessments_path_module', 'assessments', ['learning_path_id', 'module_id'])
    op.create_index('ix_assessments_available', 'assessments', ['available_from', 'available_until'])
    
    # Create assessment_questions table
    op.create_table(
        'assessment_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stem', sa.Text(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(30), nullable=False, server_default='multiple_choice'),
        sa.Column('options', postgresql.JSON(), nullable=True),
        sa.Column('correct_answer', postgresql.JSON(), nullable=True),
        sa.Column('partial_credit_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('partial_credit_rules', postgresql.JSON(), nullable=True),
        sa.Column('difficulty', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('difficulty_label', sa.String(20), nullable=True),
        sa.Column('discrimination', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('guessing_parameter', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('cognitive_level', sa.String(30), nullable=True),
        sa.Column('points', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(500), nullable=True),
        sa.Column('media_type', sa.String(20), nullable=True),
        sa.Column('estimated_time_seconds', sa.Integer(), nullable=True),
        sa.Column('times_shown', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_correct', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_incorrect', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_time_seconds', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('item_difficulty_actual', sa.Float(), nullable=True),
        sa.Column('discrimination_actual', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for assessment_questions
    op.create_index('ix_assessment_questions_assessment', 'assessment_questions', ['assessment_id'])
    op.create_index('ix_assessment_questions_difficulty', 'assessment_questions', ['difficulty'])
    op.create_index('ix_assessment_questions_category', 'assessment_questions', ['category'])
    op.create_index('ix_assessment_questions_type', 'assessment_questions', ['question_type'])
    
    # Create assessment_attempts table
    op.create_table(
        'assessment_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(20), nullable=False, server_default='not_started'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('question_ids', postgresql.JSON(), nullable=False),
        sa.Column('current_question_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('answered_questions', postgresql.JSON(), nullable=True),
        sa.Column('flagged_questions', postgresql.JSON(), nullable=True),
        sa.Column('raw_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('percentage_score', sa.Float(), nullable=True),
        sa.Column('scaled_score', sa.Float(), nullable=True),
        sa.Column('passing_score', sa.Float(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('points_earned', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_points', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('correct_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('incorrect_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('feedback_provided', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('explanations_shown', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('review_available', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for assessment_attempts
    op.create_index('ix_attempts_user_assessment', 'assessment_attempts', ['user_id', 'assessment_id'])
    op.create_index('ix_attempts_status', 'assessment_attempts', ['status'])
    op.create_index('ix_attempts_started', 'assessment_attempts', ['started_at'])
    op.create_index('ix_attempts_submitted', 'assessment_attempts', ['submitted_at'])
    
    # Create answers table
    op.create_table(
        'answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answer', postgresql.JSON(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('partial_score', sa.Float(), nullable=True),
        sa.Column('points_earned', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_points', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('question_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('is_skipped', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('was_changed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('explanation_shown', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('correct_answer_shown', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_graded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('graded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('grading_notes', sa.Text(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for answers
    op.create_index('ix_answers_attempt', 'answers', ['attempt_id'])
    op.create_index('ix_answers_question', 'answers', ['question_id'])
    op.create_index('ix_answers_attempt_question', 'answers', ['attempt_id', 'question_id'], unique=True)


def downgrade() -> None:
    # Drop answers table
    op.drop_index('ix_answers_attempt_question', table_name='answers')
    op.drop_index('ix_answers_question', table_name='answers')
    op.drop_index('ix_answers_attempt', table_name='answers')
    op.drop_table('answers')
    
    # Drop assessment_attempts table
    op.drop_index('ix_attempts_submitted', table_name='assessment_attempts')
    op.drop_index('ix_attempts_started', table_name='assessment_attempts')
    op.drop_index('ix_attempts_status', table_name='assessment_attempts')
    op.drop_index('ix_attempts_user_assessment', table_name='assessment_attempts')
    op.drop_table('assessment_attempts')
    
    # Drop assessment_questions table
    op.drop_index('ix_assessment_questions_type', table_name='assessment_questions')
    op.drop_index('ix_assessment_questions_category', table_name='assessment_questions')
    op.drop_index('ix_assessment_questions_difficulty', table_name='assessment_questions')
    op.drop_index('ix_assessment_questions_assessment', table_name='assessment_questions')
    op.drop_table('assessment_questions')
    
    # Drop assessments table
    op.drop_index('ix_assessments_available', table_name='assessments')
    op.drop_index('ix_assessments_path_module', table_name='assessments')
    op.drop_index('ix_assessments_content', table_name='assessments')
    op.drop_index('ix_assessments_status_created', table_name='assessments')
    op.drop_table('assessments')
