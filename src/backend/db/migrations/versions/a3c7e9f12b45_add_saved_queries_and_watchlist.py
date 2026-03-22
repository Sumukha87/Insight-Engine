"""add_saved_queries_and_entity_watchlist

Revision ID: a3c7e9f12b45
Revises: fe2ed240346d
Create Date: 2026-03-22 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a3c7e9f12b45"
down_revision: Union[str, None] = "fe2ed240346d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("result_json", postgresql.JSONB, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_saved_queries_user_id", "saved_queries", ["user_id"])
    op.create_index("ix_saved_queries_created_at", "saved_queries", ["created_at"])

    op.create_table(
        "entity_watchlist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_name", sa.String(500), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_domain", sa.String(100), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_entity_watchlist_user_id", "entity_watchlist", ["user_id"])
    op.create_unique_constraint(
        "uq_watchlist_user_entity", "entity_watchlist", ["user_id", "entity_name"]
    )


def downgrade() -> None:
    op.drop_table("entity_watchlist")
    op.drop_table("saved_queries")
