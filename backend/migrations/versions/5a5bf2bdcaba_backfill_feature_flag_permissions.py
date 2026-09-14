"""backfill feature flag permissions

Revision ID: 5a5bf2bdcaba
Revises: c270fea90fb2
Create Date: 2026-09-14 14:43:21.677907
"""

from collections.abc import Sequence

from alembic import op

revision: str = "5a5bf2bdcaba"
down_revision: str | None = "c270fea90fb2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO core_permissions (id, code, description)
        VALUES
            (gen_random_uuid(), 'features.read', 'View feature flags'),
            (gen_random_uuid(), 'features.manage', 'Manage feature flags')
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO core_role_permissions (role_id, permission_id)
        SELECT roles.id, permissions.id
        FROM core_roles AS roles
        JOIN core_permissions AS permissions
          ON permissions.code IN ('features.read', 'features.manage')
        WHERE roles.name IN ('owner', 'admin')
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO core_role_permissions (role_id, permission_id)
        SELECT roles.id, permissions.id
        FROM core_roles AS roles
        JOIN core_permissions AS permissions
          ON permissions.code = 'features.read'
        WHERE roles.name IN ('manager', 'viewer')
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM core_role_permissions
        WHERE permission_id IN (
            SELECT id FROM core_permissions
            WHERE code IN ('features.read', 'features.manage')
        )
        """
    )
    op.execute(
        """
        DELETE FROM core_permissions
        WHERE code IN ('features.read', 'features.manage')
        """
    )
