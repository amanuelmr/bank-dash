"""link refresh tokens into session families

Adds `refresh_tokens.family_id` so that every token descended from one sign-in
can be identified and revoked together. Rotation was already single-use, but a
replayed token was rejected while the tokens the attacker had rotated it to kept
working - so stealing one refresh token still handed over a renewable session.

Existing rows each become their own family. That preserves current behaviour
exactly: no pre-existing token is linked to another, so a replay of an old token
cannot retroactively revoke a chain it was never part of.

Revision ID: b7d2c41e9a05
Revises: 6a1e778703fd
Create Date: 2026-10-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d2c41e9a05"
down_revision: Union[str, Sequence[str], None] = "6a1e778703fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable first: existing rows have no family to point at, and NOT NULL
    # cannot be added until they all have one.
    op.add_column(
        "refresh_tokens",
        sa.Column("family_id", sa.String(length=36), nullable=True),
    )

    # Every existing token starts a family of its own, which is the conservative
    # choice - it cannot link two tokens that were never related.
    op.execute(sa.text("UPDATE refresh_tokens SET family_id = id"))

    # SQLite cannot ALTER a column's constraints at all, and this project runs on
    # SQLite by default. batch_alter_table detects that and rebuilds the table
    # instead, so the same migration works on both engines.
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.alter_column("family_id", nullable=False)

    op.create_index(
        "ix_refresh_tokens_family_id",
        "refresh_tokens",
        ["family_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "family_id")