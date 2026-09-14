from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.context import OrganizationContext
from app.core.persistence.models import AuditEvent, FeatureFlag, Membership, Role, User


class SqlAlchemyManagementRepository:
    def __init__(self, session: AsyncSession, context: OrganizationContext) -> None:
        self._session = session
        self.context = context

    async def list_members(self) -> Sequence[tuple[Membership, User, Role]]:
        statement = (
            select(Membership, User, Role)
            .join(User, User.id == Membership.user_id)
            .join(
                Role,
                (Role.id == Membership.role_id)
                & (Role.organization_id == Membership.organization_id),
            )
            .where(Membership.organization_id == self.context.organization_id)
            .order_by(User.email)
        )
        return tuple((await self._session.execute(statement)).tuples().all())

    async def add_member(self, email: str, role_name: str) -> str:
        user = await self._session.scalar(select(User).where(User.email == email))
        role = await self._session.scalar(
            select(Role).where(
                Role.organization_id == self.context.organization_id,
                Role.name == role_name,
            )
        )
        if user is None or role is None:
            return "not_found"
        existing = await self._session.scalar(
            select(Membership.id).where(
                Membership.organization_id == self.context.organization_id,
                Membership.user_id == user.id,
            )
        )
        if existing is not None:
            return "conflict"
        membership = Membership(
            organization_id=self.context.organization_id,
            user_id=user.id,
            role_id=role.id,
        )
        self._session.add(membership)
        await self._session.flush()
        self._audit("membership.created", "membership", str(membership.id))
        return "created"

    async def change_member_role(self, membership_id: UUID, role_name: str) -> str:
        membership = await self._session.scalar(
            select(Membership).where(
                Membership.id == membership_id,
                Membership.organization_id == self.context.organization_id,
            )
        )
        role = await self._session.scalar(
            select(Role).where(
                Role.organization_id == self.context.organization_id,
                Role.name == role_name,
            )
        )
        if membership is None or role is None:
            return "not_found"
        current_role = await self._session.get(Role, membership.role_id)
        if current_role is not None and current_role.name == "owner" and role.name != "owner":
            owner_count = await self._session.scalar(
                select(func.count())
                .select_from(Membership)
                .join(Role, Role.id == Membership.role_id)
                .where(
                    Membership.organization_id == self.context.organization_id,
                    Membership.is_active.is_(True),
                    Role.name == "owner",
                )
            )
            if owner_count == 1:
                return "last_owner"
        membership.role_id = role.id
        self._audit("membership.role_changed", "membership", str(membership.id))
        return "updated"

    async def list_flags(self) -> Sequence[FeatureFlag]:
        statement = (
            select(FeatureFlag)
            .where(FeatureFlag.organization_id == self.context.organization_id)
            .order_by(FeatureFlag.key)
        )
        return tuple((await self._session.scalars(statement)).all())

    async def set_flag(self, key: str, enabled: bool) -> None:
        flag = await self._session.scalar(
            select(FeatureFlag).where(
                FeatureFlag.organization_id == self.context.organization_id,
                FeatureFlag.key == key,
            )
        )
        if flag is None:
            flag = FeatureFlag(
                organization_id=self.context.organization_id,
                key=key,
            )
            self._session.add(flag)
        flag.enabled = enabled
        await self._session.flush()
        self._audit("feature_flag.updated", "feature_flag", key)

    async def list_audit_events(self) -> Sequence[AuditEvent]:
        statement = (
            select(AuditEvent)
            .where(AuditEvent.organization_id == self.context.organization_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(100)
        )
        return tuple((await self._session.scalars(statement)).all())

    def _audit(self, action: str, resource_type: str, resource_id: str) -> None:
        self._session.add(
            AuditEvent(
                organization_id=self.context.organization_id,
                actor_id=self.context.actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result="success",
            )
        )

    async def commit(self) -> None:
        await self._session.commit()
