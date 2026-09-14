from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.authorization import APPLICATIONS, PERMISSIONS, ROLE_PERMISSIONS
from app.core.domain.enums import MembershipRole
from app.core.persistence.models import (
    Application,
    AuditEvent,
    AuthSession,
    Membership,
    Organization,
    OrganizationApplication,
    PasswordResetToken,
    Permission,
    Role,
    User,
)


@dataclass(frozen=True, slots=True)
class StoredIdentity:
    user: User
    organization: Organization
    membership: Membership


class SqlAlchemyAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def email_exists(self, email: str) -> bool:
        return await self._session.scalar(select(User.id).where(User.email == email)) is not None

    async def slug_exists(self, slug: str) -> bool:
        statement = select(Organization.id).where(Organization.slug == slug)
        return await self._session.scalar(statement) is not None

    async def create_owner_account(
        self,
        *,
        email: str,
        password_hash: str,
        organization_name: str,
        organization_slug: str,
    ) -> tuple[User, Organization]:
        user = User(email=email, password_hash=password_hash)
        organization = Organization(name=organization_name, slug=organization_slug)
        self._session.add_all([user, organization])
        await self._session.flush()

        permissions = list(
            (
                await self._session.scalars(
                    select(Permission).where(Permission.code.in_(PERMISSIONS))
                )
            ).all()
        )
        known_permission_codes = {permission.code for permission in permissions}
        permissions.extend(
            Permission(code=code, description=description)
            for code, description in PERMISSIONS.items()
            if code not in known_permission_codes
        )
        self._session.add_all(permissions)
        await self._session.flush()
        permissions_by_code = {permission.code: permission for permission in permissions}

        roles = []
        for role_name in MembershipRole:
            role = Role(organization_id=organization.id, name=role_name.value)
            role.permissions = [
                permissions_by_code[code] for code in ROLE_PERMISSIONS[role_name]
            ]
            roles.append(role)
        self._session.add_all(roles)
        await self._session.flush()

        applications = list((await self._session.scalars(select(Application))).all())
        known_app_codes = {application.code for application in applications}
        applications.extend(
            Application(code=code, name=name)
            for code, name in APPLICATIONS.items()
            if code not in known_app_codes
        )
        self._session.add_all(applications)
        await self._session.flush()
        core_app = next(application for application in applications if application.code == "core")
        self._session.add(
            OrganizationApplication(
                organization_id=organization.id,
                app_id=core_app.id,
                enabled=True,
            )
        )

        owner_role = next(role for role in roles if role.name == MembershipRole.OWNER)
        self._session.add(
            Membership(
                organization_id=organization.id,
                user_id=user.id,
                role_id=owner_role.id,
            )
        )
        return user, organization

    async def find_login_identity(self, email: str, slug: str) -> StoredIdentity | None:
        statement = (
            select(User, Organization, Membership)
            .join(Membership, Membership.user_id == User.id)
            .join(Organization, Organization.id == Membership.organization_id)
            .where(
                User.email == email,
                Organization.slug == slug,
                User.is_active.is_(True),
                Organization.is_active.is_(True),
                Membership.is_active.is_(True),
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        return StoredIdentity(*row) if row is not None else None

    async def add_session(self, session: AuthSession) -> None:
        self._session.add(session)
        await self._session.flush()

    def add_audit_event(self, event: AuditEvent) -> None:
        self._session.add(event)

    async def get_authenticated_identity(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        membership_id: UUID,
        session_id: UUID,
        token_hash: str,
    ) -> StoredIdentity | None:
        now = datetime.now(UTC)
        statement = (
            select(User, Organization, Membership)
            .join(
                Membership,
                (Membership.id == membership_id)
                & (Membership.user_id == User.id)
                & (Membership.organization_id == organization_id),
            )
            .join(Organization, Organization.id == Membership.organization_id)
            .join(
                AuthSession,
                (AuthSession.id == session_id)
                & (AuthSession.user_id == User.id)
                & (AuthSession.token_hash == token_hash),
            )
            .where(
                User.id == user_id,
                User.is_active.is_(True),
                Organization.is_active.is_(True),
                Membership.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        return StoredIdentity(*row) if row is not None else None

    async def revoke_session(self, session_id: UUID) -> None:
        statement = (
            update(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.execute(statement)

    async def find_user_by_email(self, email: str) -> User | None:
        return cast(
            User | None,
            await self._session.scalar(
                select(User).where(User.email == email, User.is_active.is_(True))
            ),
        )

    async def invalidate_password_resets(self, user_id: UUID) -> None:
        await self._session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )

    def add_password_reset(self, reset: PasswordResetToken) -> None:
        self._session.add(reset)

    async def consume_password_reset(self, token_hash: str, password_hash: str) -> bool:
        now = datetime.now(UTC)
        reset = await self._session.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
        if reset is None:
            return False
        user = await self._session.get(User, reset.user_id)
        if user is None or not user.is_active:
            return False
        user.password_hash = password_hash
        reset.used_at = now
        await self._session.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        memberships = (
            await self._session.scalars(
                select(Membership).where(
                    Membership.user_id == user.id,
                    Membership.is_active.is_(True),
                )
            )
        ).all()
        for membership in memberships:
            self.add_audit_event(
                AuditEvent(
                    organization_id=membership.organization_id,
                    actor_id=user.id,
                    action="identity.password_reset",
                    resource_type="user",
                    resource_id=str(user.id),
                    result="success",
                )
            )
        return True

    async def commit(self) -> None:
        await self._session.commit()
