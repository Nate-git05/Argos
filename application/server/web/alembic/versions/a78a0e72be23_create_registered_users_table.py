"""create registered_users table

Revision ID: a78a0e72be23
Revises: 
Create Date: 2026-08-01 18:06:39.463410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a78a0e72be23'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "registered_users",
        sa.Column("id", sa.Integer(), primary_key=True),  # auto-incrementing primary key
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),  # one registration per email
        sa.Column(
            "registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),  # audit column, set by Postgres itself on insert
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("registered_users")  # reverses upgrade() -- drops the whole table
