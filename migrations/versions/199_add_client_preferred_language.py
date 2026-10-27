"""Add a preferred language per client (portal default and client emails).

Revision ID: 199_add_client_preferred_language
Revises: 198_add_oauth_applications
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "199_add_client_preferred_language"
down_revision = "198_add_oauth_applications"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    try:
        return column_name in {c["name"] for c in inspector.get_columns(table_name)}
    except Exception:
        return False


def upgrade():
    inspector = inspect(op.get_bind())
    if "clients" in inspector.get_table_names() and not _has_column(inspector, "clients", "preferred_language"):
        op.add_column("clients", sa.Column("preferred_language", sa.String(length=10), nullable=True))


def downgrade():
    inspector = inspect(op.get_bind())
    if "clients" in inspector.get_table_names() and _has_column(inspector, "clients", "preferred_language"):
        op.drop_column("clients", "preferred_language")
