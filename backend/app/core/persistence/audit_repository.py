from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.context import OrganizationContext
from app.core.persistence.models import AuditEvent


class SqlAlchemyAuditEventRepository:
    """Tenant-scoped audit adapter; tenant scope is never accepted per query."""

    def __init__(self, session: AsyncSession, context: OrganizationContext) -> None:
        self._session = session
        self.context = context

    async def list(self) -> Sequence[AuditEvent]:
        statement = (
            select(AuditEvent)
            .where(AuditEvent.organization_id == self.context.organization_id)
            .order_by(AuditEvent.created_at.desc())
        )
        return tuple((await self._session.scalars(statement)).all())

