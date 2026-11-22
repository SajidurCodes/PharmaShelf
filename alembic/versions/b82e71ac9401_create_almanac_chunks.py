"""Create Almanac chunks for semantic retrieval."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR

revision = "b82e71ac9401"
down_revision = "776b22e67428"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "almanac_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "entry_id",
            sa.Uuid(),
            sa.ForeignKey("almanac_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", VECTOR(384), nullable=False),
        sa.UniqueConstraint("entry_id", "chunk_index", name="uq_almanac_chunk_position"),
        sa.CheckConstraint("chunk_index >= 0", name="ck_almanac_chunk_index"),
    )


def downgrade() -> None:
    op.drop_table("almanac_chunks")
