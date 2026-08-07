"""Update assessment statistics triggers

Revision ID: 000002
Revises: 000001
Create Date: 2025-08-05

This migration adds functions and triggers to automatically update
assessment statistics when questions are added/removed or when
attempts are submitted.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '000002'
down_revision: Union[str, None] = '000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create function to update assessment question count
    op.execute("""
        CREATE OR REPLACE FUNCTION update_assessment_question_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE assessments 
                SET question_count = question_count + 1,
                    updated_at = NOW()
                WHERE id = NEW.assessment_id;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE assessments 
                SET question_count = question_count - 1,
                    updated_at = NOW()
                WHERE id = OLD.assessment_id;
                RETURN OLD;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for question count
    op.execute("""
        CREATE TRIGGER trigger_update_assessment_question_count
        AFTER INSERT OR DELETE ON assessment_questions
        FOR EACH ROW EXECUTE FUNCTION update_assessment_question_count();
    """)
    
    # Create function to update attempt statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION update_attempt_statistics()
        RETURNS TRIGGER AS $$
        DECLARE
            v_assessment_id UUID;
            v_correct_count INTEGER;
            v_total_count INTEGER;
            v_score FLOAT;
            v_passed BOOLEAN;
        BEGIN
            -- Get assessment ID based on trigger operation
            IF TG_OP = 'INSERT' THEN
                v_assessment_id := NEW.attempt_id;
            ELSE
                v_assessment_id := OLD.attempt_id;
            END IF;
            
            -- Get the assessment_id from the attempt
            SELECT assessment_id INTO v_assessment_id
            FROM assessment_attempts
            WHERE id = v_assessment_id;
            
            -- Calculate statistics
            SELECT 
                COUNT(*) FILTER (WHERE is_correct = true),
                COUNT(*),
                COALESCE(AVG(percentage_score), 0),
                COUNT(*) FILTER (WHERE passed = true)
            INTO v_correct_count, v_total_count, v_score, v_passed
            FROM assessment_attempts
            WHERE assessment_id = v_assessment_id
            AND status IN ('submitted', 'graded');
            
            -- Update assessment statistics
            UPDATE assessments
            SET 
                total_attempts = v_total_count,
                completed_attempts = v_total_count,
                average_score = v_score,
                completion_rate = CASE WHEN total_attempts > 0 
                    THEN (v_total_count::FLOAT / total_attempts) * 100 
                    ELSE 0 END,
                pass_rate = CASE WHEN v_total_count > 0 
                    THEN (v_passed::FLOAT / v_total_count) * 100 
                    ELSE 0 END,
                updated_at = NOW()
            WHERE id = v_assessment_id;
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for attempt updates
    op.execute("""
        CREATE TRIGGER trigger_update_attempt_statistics
        AFTER INSERT OR UPDATE OF status, percentage_score, passed ON assessment_attempts
        FOR EACH ROW 
        WHEN (NEW.status IN ('submitted', 'graded', 'expired'))
        EXECUTE FUNCTION update_attempt_statistics();
    """)
    
    # Create function to update question statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION update_question_statistics()
        RETURNS TRIGGER AS $$
        DECLARE
            v_times_shown INTEGER;
            v_times_correct INTEGER;
            v_avg_time FLOAT;
        BEGIN
            -- Calculate statistics from answers
            SELECT 
                COUNT(*),
                COUNT(*) FILTER (WHERE is_correct = true),
                COALESCE(AVG(time_spent_seconds), 0)
            INTO v_times_shown, v_times_correct, v_avg_time
            FROM answers
            WHERE question_id = COALESCE(NEW.question_id, OLD.question_id);
            
            -- Update question statistics
            UPDATE assessment_questions
            SET 
                times_shown = v_times_shown,
                times_correct = v_times_correct,
                times_incorrect = v_times_shown - v_times_correct,
                average_time_seconds = v_avg_time,
                success_rate = CASE WHEN v_times_shown > 0 
                    THEN v_times_correct::FLOAT / v_times_shown 
                    ELSE 0 END,
                updated_at = NOW()
            WHERE id = COALESCE(NEW.question_id, OLD.question_id);
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for answer updates
    op.execute("""
        CREATE TRIGGER trigger_update_question_statistics
        AFTER INSERT OR UPDATE OF is_correct ON answers
        FOR EACH ROW EXECUTE FUNCTION update_question_statistics();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_update_question_statistics ON answers;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_attempt_statistics ON assessment_attempts;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_assessment_question_count ON assessment_questions;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_question_statistics();")
    op.execute("DROP FUNCTION IF EXISTS update_attempt_statistics();")
    op.execute("DROP FUNCTION IF EXISTS update_assessment_question_count();")
