"""create commercial crm

Revision ID: 8bd1a42f937e
Revises: 5a5bf2bdcaba
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8bd1a42f937e"
down_revision: str | None = "5a5bf2bdcaba"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _identity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
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
    ]


def upgrade() -> None:
    op.create_table(
        "commercial_companies",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("domain", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(320)),
        sa.Column("city", sa.String(120)),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("qualification_score", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text()),
        *_identity_columns(),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "domain", name="uq_commercial_company_org_domain"),
    )
    op.create_index(
        "ix_commercial_company_org_name", "commercial_companies", ["organization_id", "name"]
    )
    op.create_table(
        "commercial_opportunities",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(30), nullable=False),
        sa.Column("value", sa.Numeric(12, 2)),
        sa.Column("next_best_action", sa.String(255)),
        sa.Column("next_action_at", sa.DateTime(timezone=True)),
        *_identity_columns(),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["commercial_companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )
    op.create_index(
        "ix_commercial_opportunity_org_stage",
        "commercial_opportunities",
        ["organization_id", "stage"],
    )
    op.create_index(
        "ix_commercial_opportunities_next_action_at", "commercial_opportunities", ["next_action_at"]
    )
    op.create_table(
        "commercial_contacts",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(120)),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(50)),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        *_identity_columns(),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["commercial_companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commercial_contacts_organization_id", "commercial_contacts", ["organization_id"]
    )
    op.create_table(
        "commercial_activities",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["commercial_companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["core_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commercial_activity_org_company",
        "commercial_activities",
        ["organization_id", "company_id"],
    )
    op.create_table(
        "commercial_calls",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["commercial_companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["core_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commercial_calls_organization_id", "commercial_calls", ["organization_id"])
    for table, extra in (
        (
            "commercial_tasks",
            [
                sa.Column("company_id", sa.Uuid(), nullable=False),
                sa.Column("title", sa.String(255), nullable=False),
                sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("completed_at", sa.DateTime(timezone=True)),
            ],
        ),
        ("commercial_tags", [sa.Column("name", sa.String(80), nullable=False)]),
        (
            "commercial_campaigns",
            [
                sa.Column("name", sa.String(160), nullable=False),
                sa.Column("status", sa.String(30), nullable=False),
            ],
        ),
    ):
        constraints: list[object] = [
            sa.ForeignKeyConstraint(
                ["organization_id"], ["core_organizations.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        ]
        if table == "commercial_tasks":
            constraints.append(
                sa.ForeignKeyConstraint(
                    ["company_id"], ["commercial_companies.id"], ondelete="CASCADE"
                )
            )
        if table == "commercial_tags":
            constraints.append(sa.UniqueConstraint("organization_id", "name"))
        op.create_table(
            table,
            sa.Column("organization_id", sa.Uuid(), nullable=False),
            *extra,
            *_identity_columns(),
            *constraints,
        )
        op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])

    op.execute(
        """
        INSERT INTO core_permissions (id, code, description) VALUES
          (gen_random_uuid(), 'commercial.read', 'View commercial CRM records'),
          (gen_random_uuid(), 'commercial.write', 'Create and update commercial CRM records')
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO core_role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM core_roles r CROSS JOIN core_permissions p
        WHERE (r.name IN ('owner','admin','manager','employee')
               AND p.code IN ('commercial.read','commercial.write'))
           OR (r.name = 'viewer' AND p.code = 'commercial.read')
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM core_role_permissions WHERE permission_id IN
          (SELECT id FROM core_permissions
           WHERE code IN ('commercial.read','commercial.write'))
        """
    )
    op.execute("DELETE FROM core_permissions WHERE code IN ('commercial.read','commercial.write')")
    for table in (
        "commercial_campaigns",
        "commercial_tags",
        "commercial_tasks",
        "commercial_calls",
        "commercial_activities",
        "commercial_contacts",
        "commercial_opportunities",
        "commercial_companies",
    ):
        op.drop_table(table)
