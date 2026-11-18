"""Rejoin the fork's client-language branch with upstream's chain at 213.

199_add_client_preferred_language exists only in this fork and was authored off
198_add_oauth_applications. Upstream continued from 198 with its own 199..213,
which leaves two heads. Databases already stamped with the fork revision must
still run upstream's 199..213, so the fork revision keeps its place and this
no-op merge joins the two branches.

Each later upstream release that adds migrations needs another merge like this
one, with (upstream's new head, the previous fork merge) as its parents; editing
this file instead would make stamped databases skip upstream's new revisions.

Revision ID: fork_merge_213_client_language
Revises: 213_crm_communication_templates, 199_add_client_preferred_language
"""

revision = "fork_merge_213_client_language"
down_revision = (
    "213_crm_communication_templates",
    "199_add_client_preferred_language",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
