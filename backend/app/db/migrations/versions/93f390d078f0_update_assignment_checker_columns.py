"""update_assignment_checker_columns

Revision ID: 93f390d078f0
Revises: 14f1f6fe2b36
Create Date: 2026-07-20 11:14:35.209534

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93f390d078f0'
down_revision: Union[str, None] = '14f1f6fe2b36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to assignments
    op.add_column('assignments', sa.Column('instructions', sa.Text(), nullable=True))
    op.add_column('assignments', sa.Column('is_published', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('assignments', sa.Column('rubric', sa.JSON(), nullable=True))
    op.add_column('assignments', sa.Column('reference_material_id', sa.UUID(), nullable=True))

    # Add columns to assignment_submissions
    op.add_column('assignment_submissions', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
    op.add_column('assignment_submissions', sa.Column('is_final', sa.Boolean(), server_default='1', nullable=False))
    op.add_column('assignment_submissions', sa.Column('processing_status', sa.String(length=50), server_default='pending', nullable=False))

    # Add columns to assignment_feedback
    op.add_column('assignment_feedback', sa.Column('ai_score', sa.Float(), nullable=True))
    op.add_column('assignment_feedback', sa.Column('final_score', sa.Float(), nullable=True))
    op.add_column('assignment_feedback', sa.Column('is_approved', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('assignment_feedback', sa.Column('status', sa.String(length=50), server_default='pending_teacher_review', nullable=False))
    op.add_column('assignment_feedback', sa.Column('rubric_evaluation', sa.JSON(), nullable=True))
    op.add_column('assignment_feedback', sa.Column('strengths', sa.JSON(), nullable=True))
    op.add_column('assignment_feedback', sa.Column('weaknesses', sa.JSON(), nullable=True))
    op.add_column('assignment_feedback', sa.Column('grammar_feedback', sa.JSON(), nullable=True))
    op.add_column('assignment_feedback', sa.Column('suggestions', sa.JSON(), nullable=True))
    op.add_column('assignment_feedback', sa.Column('similarity_report', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('assignment_feedback', 'similarity_report')
    op.drop_column('assignment_feedback', 'suggestions')
    op.drop_column('assignment_feedback', 'grammar_feedback')
    op.drop_column('assignment_feedback', 'weaknesses')
    op.drop_column('assignment_feedback', 'strengths')
    op.drop_column('assignment_feedback', 'rubric_evaluation')
    op.drop_column('assignment_feedback', 'status')
    op.drop_column('assignment_feedback', 'is_approved')
    op.drop_column('assignment_feedback', 'final_score')
    op.drop_column('assignment_feedback', 'ai_score')

    op.drop_column('assignment_submissions', 'processing_status')
    op.drop_column('assignment_submissions', 'is_final')
    op.drop_column('assignment_submissions', 'version')

    op.drop_column('assignments', 'reference_material_id')
    op.drop_column('assignments', 'rubric')
    op.drop_column('assignments', 'is_published')
    op.drop_column('assignments', 'instructions')
