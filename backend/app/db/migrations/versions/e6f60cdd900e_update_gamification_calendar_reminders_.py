"""update_gamification_calendar_reminders_tables

Revision ID: e6f60cdd900e
Revises: 84d983d1f144
Create Date: 2026-07-20 12:00:59.102131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f60cdd900e'
down_revision: Union[str, None] = '84d983d1f144'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('calendar_events',
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_completed', sa.Boolean(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_events_id'), 'calendar_events', ['id'], unique=False)
    op.create_index(op.f('ix_calendar_events_is_deleted'), 'calendar_events', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'], unique=False)

    op.create_table('smart_reminders',
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('reminder_type', sa.String(length=50), nullable=False),
    sa.Column('remind_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_triggered', sa.Boolean(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_smart_reminders_id'), 'smart_reminders', ['id'], unique=False)
    op.create_index(op.f('ix_smart_reminders_is_deleted'), 'smart_reminders', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_smart_reminders_user_id'), 'smart_reminders', ['user_id'], unique=False)

    op.create_table('user_gamification',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('xp_points', sa.Integer(), nullable=False),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('current_streak', sa.Integer(), nullable=False),
    sa.Column('longest_streak', sa.Integer(), nullable=False),
    sa.Column('badges', sa.JSON(), nullable=True),
    sa.Column('achievements', sa.JSON(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_gamification_id'), 'user_gamification', ['id'], unique=False)
    op.create_index(op.f('ix_user_gamification_is_deleted'), 'user_gamification', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_user_gamification_user_id'), 'user_gamification', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_gamification_user_id'), table_name='user_gamification')
    op.drop_index(op.f('ix_user_gamification_is_deleted'), table_name='user_gamification')
    op.drop_index(op.f('ix_user_gamification_id'), table_name='user_gamification')
    op.drop_table('user_gamification')

    op.drop_index(op.f('ix_smart_reminders_user_id'), table_name='smart_reminders')
    op.drop_index(op.f('ix_smart_reminders_is_deleted'), table_name='smart_reminders')
    op.drop_index(op.f('ix_smart_reminders_id'), table_name='smart_reminders')
    op.drop_table('smart_reminders')

    op.drop_index(op.f('ix_calendar_events_user_id'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_is_deleted'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_id'), table_name='calendar_events')
    op.drop_table('calendar_events')
