from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.application.apps import AuthorizationError
from app.core.application.auth import AuthenticatedIdentity
from app.core.exceptions import ProcessOSError
from app.core.persistence.management_repository import SqlAlchemyManagementRepository
from app.core.persistence.models import AuditEvent


class ManagementConflictError(ProcessOSError):
    pass


class ManagementNotFoundError(ProcessOSError):
    pass


@dataclass(frozen=True, slots=True)
class MemberView:
    id: UUID
    user_id: UUID
    email: str
    role: str
    active: bool


@dataclass(frozen=True, slots=True)
class FeatureFlagView:
    key: str
    enabled: bool


class CoreManagementService:
    def __init__(
        self,
        repository: SqlAlchemyManagementRepository,
        identity: AuthenticatedIdentity,
    ) -> None:
        self._repository = repository
        self._identity = identity

    def _require(self, permission: str) -> None:
        if permission not in self._identity.permissions:
            raise AuthorizationError(f"Missing permission: {permission}")

    async def list_members(self) -> tuple[MemberView, ...]:
        self._require("members.read")
        rows = await self._repository.list_members()
        return tuple(
            MemberView(
                id=membership.id,
                user_id=user.id,
                email=user.email,
                role=role.name,
                active=membership.is_active,
            )
            for membership, user, role in rows
        )

    async def add_member(self, email: str, role: str) -> None:
        self._require("members.manage")
        result = await self._repository.add_member(email, role)
        if result == "not_found":
            raise ManagementNotFoundError("User or role does not exist")
        if result == "conflict":
            raise ManagementConflictError("User is already a member")
        await self._repository.commit()

    async def change_member_role(self, membership_id: UUID, role: str) -> None:
        self._require("roles.manage")
        result = await self._repository.change_member_role(membership_id, role)
        if result == "not_found":
            raise ManagementNotFoundError("Membership or role does not exist")
        if result == "last_owner":
            raise ManagementConflictError("The last owner cannot be demoted")
        await self._repository.commit()

    async def list_flags(self) -> tuple[FeatureFlagView, ...]:
        self._require("features.read")
        flags = await self._repository.list_flags()
        return tuple(FeatureFlagView(key=flag.key, enabled=flag.enabled) for flag in flags)

    async def set_flag(self, key: str, enabled: bool) -> None:
        self._require("features.manage")
        await self._repository.set_flag(key, enabled)
        await self._repository.commit()

    async def list_audit_events(self) -> Sequence[AuditEvent]:
        self._require("audit.read")
        return await self._repository.list_audit_events()


@dataclass(frozen=True, slots=True)
class AuditEventView:
    action: str
    resource_type: str
    resource_id: str | None
    result: str
    created_at: datetime
