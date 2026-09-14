from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.context import OrganizationContext
from app.core.persistence.models import (
    Application,
    AuditEvent,
    OrganizationApplication,
)


class SqlAlchemyAppRepository:
    def __init__(self, session: AsyncSession, context: OrganizationContext) -> None:
        self._session = session
        self.context = context

    async def list_enabled(self) -> Sequence[Application]:
        statement = (
            select(Application)
            .join(OrganizationApplication, OrganizationApplication.app_id == Application.id)
            .where(
                OrganizationApplication.organization_id == self.context.organization_id,
                OrganizationApplication.enabled.is_(True),
                Application.is_active.is_(True),
            )
            .order_by(Application.name)
        )
        return tuple((await self._session.scalars(statement)).all())

    async def set_enabled(self, code: str, enabled: bool) -> bool:
        application = await self._session.scalar(
            select(Application).where(Application.code == code, Application.is_active.is_(True))
        )
        if application is None:
            return False
        entitlement = await self._session.scalar(
            select(OrganizationApplication).where(
                OrganizationApplication.organization_id == self.context.organization_id,
                OrganizationApplication.app_id == application.id,
            )
        )
        if entitlement is None:
            entitlement = OrganizationApplication(
                organization_id=self.context.organization_id,
                app_id=application.id,
            )
            self._session.add(entitlement)
        entitlement.enabled = enabled
        return True

    async def record_change(self, *, actor_id: UUID, app_code: str, enabled: bool) -> None:
        self._session.add(
            AuditEvent(
                organization_id=self.context.organization_id,
                actor_id=actor_id,
                action="app.enabled" if enabled else "app.disabled",
                resource_type="application",
                resource_id=app_code,
                result="success",
            )
        )

    async def commit(self) -> None:
        await self._session.commit()
