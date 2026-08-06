"""update_quiz_assessment_columns

Revision ID: 2f5fcb89c374
Revises: 93f390d078f0
Create Date: 2026-07-20 11:28:45.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f5fcb89c374'
down_revision: Union[str, None] = '93f390d078f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to quizzes
    op.add_column('quizzes', sa.Column('is_published', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('quizzes', sa.Column('difficulty', sa.String(length=30), server_default='mixed', nullable=False))
    op.add_column('quizzes', sa.Column('blooms_level', sa.JSON(), nullable=True))
    op.add_column('quizzes', sa.Column('negative_marking', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('quizzes', sa.Column('passing_percentage', sa.Float(), server_default='40.0', nullable=False))
    op.add_column('quizzes', sa.Column('max_attempts', sa.Integer(), server_default='1', nullable=False))
    op.add_column('quizzes', sa.Column('randomize_questions', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('quizzes', sa.Column('randomize_options', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('quizzes', sa.Column('topic', sa.String(length=255), nullable=True))
    op.add_column('quizzes', sa.Column('source_notes_id', sa.UUID(), nullable=True))

    # Add columns to quiz_questions
    op.add_column('quiz_questions', sa.Column('difficulty', sa.String(length=30), server_default='medium', nullable=False))
    op.add_column('quiz_questions', sa.Column('blooms_level', sa.String(length=50), server_default='Remember', nullable=False))
    op.add_column('quiz_questions', sa.Column('topic', sa.String(length=255), nullable=True))
    op.add_column('quiz_questions', sa.Column('estimated_time_seconds', sa.Integer(), server_default='60', nullable=False))
    op.add_column('quiz_questions', sa.Column('related_concept', sa.Text(), nullable=True))
    op.add_column('quiz_questions', sa.Column('recommended_revision_topic', sa.Text(), nullable=True))

    # Add columns to quiz_attempts
    op.add_column('quiz_attempts', sa.Column('total_points', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('quiz_attempts', sa.Column('passed', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('quiz_attempts', sa.Column('status', sa.String(length=50), server_default='in_progress', nullable=False))
    op.add_column('quiz_attempts', sa.Column('progress_data', sa.JSON(), nullable=True))

    # Add columns to quiz_answers
    op.add_column('quiz_answers', sa.Column('feedback_comments', sa.Text(), nullable=True))
    op.add_column('quiz_answers', sa.Column('teacher_override_score', sa.Float(), nullable=True))
    op.add_column('quiz_answers', sa.Column('evaluated_by_ai', sa.Boolean(), server_default='1', nullable=False))

    # Create question_bank table
    op.create_table(
        'question_bank',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=30), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('points', sa.Float(), nullable=False),
        sa.Column('difficulty', sa.String(length=30), nullable=False),
        sa.Column('blooms_level', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=True),
        sa.Column('topic', sa.String(length=255), nullable=True),
        sa.Column('creator_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('question_bank')

    op.drop_column('quiz_answers', 'evaluated_by_ai')
    op.drop_column('quiz_answers', 'teacher_override_score')
    op.drop_column('quiz_answers', 'feedback_comments')

    op.drop_column('quiz_attempts', 'progress_data')
    op.drop_column('quiz_attempts', 'status')
    op.drop_column('quiz_attempts', 'passed')
    op.drop_column('quiz_attempts', 'total_points')

    op.drop_column('quiz_questions', 'recommended_revision_topic')
    op.drop_column('quiz_questions', 'related_concept')
    op.drop_column('quiz_questions', 'estimated_time_seconds')
    op.drop_column('quiz_questions', 'topic')
    op.drop_column('quiz_questions', 'blooms_level')
    op.drop_column('quiz_questions', 'difficulty')

    op.drop_column('quizzes', 'source_notes_id')
    op.drop_column('quizzes', 'topic')
    op.drop_column('quizzes', 'randomize_options')
    op.drop_column('quizzes', 'randomize_questions')
    op.drop_column('quizzes', 'max_attempts')
    op.drop_column('quizzes', 'passing_percentage')
    op.drop_column('quizzes', 'negative_marking')
    op.drop_column('quizzes', 'blooms_level')
    op.drop_column('quizzes', 'difficulty')
    op.drop_column('quizzes', 'is_published')
