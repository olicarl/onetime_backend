"""add is_admin to users

Revision ID: 974e962c504a
Revises: b55581e0dfdc
Create Date: 2026-02-22 12:40:46.347190

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '974e962c504a'
down_revision = 'b55581e0dfdc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), server_default='true', nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
