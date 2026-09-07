"""update games schema

Revision ID: 7ac58a28590e
Revises: 398d67b006c7
Create Date: 2026-09-07 17:50:41.395845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7ac58a28590e'
down_revision: Union[str, Sequence[str], None] = '398d67b006c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "games",
        "session_id",
        new_column_name="game_id",
        existing_type=sa.Uuid(),
        existing_nullable=False,
    )

    op.add_column(
        "games",
        sa.Column(
            "ships",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("games", "ships")

    op.alter_column(
        "games",
        "game_id",
        new_column_name="session_id",
        existing_type=sa.Uuid(),
        existing_nullable=False,
    )