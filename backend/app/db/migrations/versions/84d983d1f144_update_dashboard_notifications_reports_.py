"""update_dashboard_notifications_reports_columns

Revision ID: 84d983d1f144
Revises: 2f5fcb89c374
Create Date: 2026-07-20 11:41:10.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84d983d1f144'
down_revision: Union[str, None] = '2f5fcb89c374'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to notifications
    op.add_column('notifications', sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('notifications', sa.Column('priority', sa.String(length=20), server_default='medium', nullable=False))
    op.add_column('notifications', sa.Column('category', sa.String(length=50), server_default='general', nullable=False))
    op.add_column('notifications', sa.Column('link', sa.String(length=255), nullable=True))

    # Add columns to announcements
    op.add_column('announcements', sa.Column('target_type', sa.String(length=50), server_default='course', nullable=False))
    op.add_column('announcements', sa.Column('department', sa.String(length=100), nullable=True))
    op.add_column('announcements', sa.Column('classroom_id', sa.UUID(), nullable=True))

    # Create generated_reports table
    op.create_table(
        'generated_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_name', sa.String(length=255), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('generated_by_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('generated_reports')

    op.drop_column('announcements', 'classroom_id')
    op.drop_column('announcements', 'department')
    op.drop_column('announcements', 'target_type')

    op.drop_column('notifications', 'link')
    op.drop_column('notifications', 'category')
    op.drop_column('notifications', 'priority')
    op.drop_column('notifications', 'is_archived')
