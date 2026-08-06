"""update_chat_session_and_message_columns

Revision ID: 14f1f6fe2b36
Revises: 4b05fc6f0e26
Create Date: 2026-07-18 21:08:41.209534

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14f1f6fe2b36'
down_revision: Union[str, None] = '4b05fc6f0e26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to chat_sessions
    op.add_column('chat_sessions', sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('chat_sessions', sa.Column('is_pinned', sa.Boolean(), server_default='0', nullable=False))

    # Add columns to chat_messages
    op.add_column('chat_messages', sa.Column('tokens_prompt', sa.Integer(), nullable=True))
    op.add_column('chat_messages', sa.Column('tokens_response', sa.Integer(), nullable=True))
    op.add_column('chat_messages', sa.Column('latency_ms', sa.Integer(), nullable=True))
    op.add_column('chat_messages', sa.Column('citations', sa.JSON(), nullable=True))
    op.add_column('chat_messages', sa.Column('is_bookmarked', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('chat_messages', sa.Column('feedback', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_sessions', 'is_pinned')
    op.drop_column('chat_sessions', 'is_archived')
    op.drop_column('chat_messages', 'feedback')
    op.drop_column('chat_messages', 'is_bookmarked')
    op.drop_column('chat_messages', 'citations')
    op.drop_column('chat_messages', 'latency_ms')
    op.drop_column('chat_messages', 'tokens_response')
    op.drop_column('chat_messages', 'tokens_prompt')
