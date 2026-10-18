"""add_github_access_token

Revision ID: f621b7a912c3
Revises: e510c6f803b0
Create Date: 2026-10-18 18:45:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f621b7a912c3'
down_revision: Union[str, None] = 'e510c6f803b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add github_access_token to users table if not already present
    try:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('github_access_token', sa.String(length=512), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    try:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('github_access_token')
    except Exception:
        pass
