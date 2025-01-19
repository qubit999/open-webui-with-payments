"""Add subscription fields to User model

Revision ID: ff62725b686b
Revises: 9f18df5e7ec7
Create Date: 2025-01-18 20:56:03.296620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'ff62725b686b'
down_revision: Union[str, None] = '9f18df5e7ec7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('user', sa.Column('card_last4', sa.String(), nullable=True))
    op.add_column('user', sa.Column('card_brand', sa.String(), nullable=True))
    op.add_column('user', sa.Column('card_exp_month', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('card_exp_year', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('user', 'card_last4')
    op.drop_column('user', 'card_brand')
    op.drop_column('user', 'card_exp_month')
    op.drop_column('user', 'card_exp_year')