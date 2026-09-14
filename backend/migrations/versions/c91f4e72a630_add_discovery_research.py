"""add discovery research

Revision ID: c91f4e72a630
Revises: 8bd1a42f937e
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c91f4e72a630"
down_revision: str | None = "8bd1a42f937e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
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


def tenant_fk() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["organization_id"], ["core_organizations.id"], ondelete="CASCADE"
    )


def company_fk() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["company_id"], ["commercial_companies.id"], ondelete="CASCADE")


def create_tenant_index(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])


def upgrade() -> None:
    op.create_table(
        "commercial_discovery_jobs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid()),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        *timestamps(),
        tenant_fk(),
        sa.ForeignKeyConstraint(["campaign_id"], ["commercial_campaigns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    create_tenant_index("commercial_discovery_jobs")
    op.create_table(
        "commercial_company_sources",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("source_url", sa.String(2048)),
        *timestamps(),
        tenant_fk(),
        company_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "provider", "external_id"),
    )
    create_tenant_index("commercial_company_sources")
    op.create_table(
        "commercial_research_jobs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(80)),
        *timestamps(),
        tenant_fk(),
        company_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    create_tenant_index("commercial_research_jobs")
    op.create_table(
        "commercial_website_analyses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("observed", sa.JSON(), nullable=False),
        sa.Column("hypotheses", sa.JSON(), nullable=False),
        *timestamps(),
        tenant_fk(),
        company_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    create_tenant_index("commercial_website_analyses")
    op.create_table(
        "commercial_review_analyses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("observed", sa.JSON(), nullable=False),
        sa.Column("hypotheses", sa.JSON(), nullable=False),
        *timestamps(),
        tenant_fk(),
        company_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    create_tenant_index("commercial_review_analyses")
    op.create_table(
        "commercial_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("evidence_type", sa.String(20), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(2048)),
        *timestamps(),
        tenant_fk(),
        company_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    create_tenant_index("commercial_signals")


def downgrade() -> None:
    for table in (
        "commercial_signals",
        "commercial_review_analyses",
        "commercial_website_analyses",
        "commercial_research_jobs",
        "commercial_company_sources",
        "commercial_discovery_jobs",
    ):
        op.drop_table(table)
