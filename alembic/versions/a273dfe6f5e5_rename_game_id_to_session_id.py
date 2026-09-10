"""rename game id to session id

Revision ID: a273dfe6f5e5
Revises: 7ac58a28590e
Create Date: 2026-09-10 06:02:30.044579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a273dfe6f5e5'
down_revision: Union[str, Sequence[str], None] = '7ac58a28590e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "games",
        "game_id",
        new_column_name="session_id",
        existing_type=sa.Uuid(),
        existing_nullable=False,
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "games",
        "session_id",
        new_column_name="game_id",
        existing_type=sa.Uuid(),
        existing_nullable=False,
    )
