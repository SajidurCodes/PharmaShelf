"""Create almanac entries table.

Revision ID: 776b22e67428
Revises: 3b0f942c5082
"""

from alembic import op
import sqlalchemy as sa


revision = "776b22e67428"
down_revision = "3b0f942c5082"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "almanac_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_note", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        "ix_almanac_entries_topic",
        "almanac_entries",
        ["topic"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_almanac_entries_topic", table_name="almanac_entries")
    op.drop_table("almanac_entries")