"""Create/Update user model

Revision ID: 9f18df5e7ec7
Revises: 3781e22d8b01
Create Date: 2025-01-18 04:02:01.891024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '9f18df5e7ec7'
down_revision: Union[str, None] = '3781e22d8b01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('subscription_status', sa.String(), nullable=True))
    op.add_column('user', sa.Column('subscription_ends_at', sa.BigInteger(), nullable=True))
    op.add_column('user', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'subscription_status')
    op.drop_column('user', 'subscription_ends_at')
    op.drop_column('user', 'stripe_customer_id')
    # ### end Alembic commands ###