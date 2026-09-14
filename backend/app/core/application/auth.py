from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.exceptions import ProcessOSError
from app.core.persistence.auth_repository import SqlAlchemyAuthRepository
from app.core.persistence.models import AuditEvent, AuthSession, Organization, User
from app.core.security import (
    InvalidTokenError,
    TokenService,
    hash_password,
    hash_token,
    verify_password,
)


class AuthenticationError(ProcessOSError):
    pass


class AccountConflictError(ProcessOSError):
    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    user_id: UUID
    email: str
    organization_id: UUID
    organization_name: str
    membership_id: UUID
    role: str
    permissions: frozenset[str]
    session_id: UUID


@dataclass(frozen=True, slots=True)
class IssuedToken:
    access_token: str
    expires_at: datetime


class AuthService:
    def __init__(self, repository: SqlAlchemyAuthRepository, tokens: TokenService) -> None:
        self._repository = repository
        self._tokens = tokens

    async def register_owner(
        self, *, email: str, password: str, organization_name: str, organization_slug: str
    ) -> tuple[User, Organization]:
        if await self._repository.email_exists(email) or await self._repository.slug_exists(
            organization_slug
        ):
            raise AccountConflictError("Account or organization already exists")
        user, organization = await self._repository.create_owner_account(
            email=email,
            password_hash=hash_password(password),
            organization_name=organization_name,
            organization_slug=organization_slug,
        )
        self._repository.add_audit_event(
            AuditEvent(
                organization_id=organization.id,
                actor_id=user.id,
                action="identity.owner_registered",
                resource_type="organization",
                resource_id=str(organization.id),
                result="success",
            )
        )
        await self._repository.commit()
        return user, organization

    async def login(self, *, email: str, password: str, organization_slug: str) -> IssuedToken:
        identity = await self._repository.find_login_identity(email, organization_slug)
        if identity is None or not verify_password(identity.user.password_hash, password):
            raise AuthenticationError("Invalid credentials")

        session_id = uuid4()
        token, expires_at = self._tokens.create(
            user_id=identity.user.id,
            organization_id=identity.organization.id,
            membership_id=identity.membership.id,
            session_id=session_id,
            role=identity.membership.role.name,
        )
        await self._repository.add_session(
            AuthSession(
                id=session_id,
                user_id=identity.user.id,
                token_hash=hash_token(token),
                expires_at=expires_at,
                created_at=datetime.now(UTC),
            )
        )
        self._repository.add_audit_event(
            AuditEvent(
                organization_id=identity.organization.id,
                actor_id=identity.user.id,
                action="identity.login",
                resource_type="auth_session",
                resource_id=str(session_id),
                result="success",
            )
        )
        await self._repository.commit()
        return IssuedToken(access_token=token, expires_at=expires_at)

    async def authenticate(self, token: str) -> AuthenticatedIdentity:
        try:
            claims = self._tokens.decode(token)
            user_id = UUID(str(claims["sub"]))
            organization_id = UUID(str(claims["org"]))
            membership_id = UUID(str(claims["membership"]))
            session_id = UUID(str(claims["sid"]))
        except (InvalidTokenError, KeyError, ValueError) as exc:
            raise AuthenticationError("Invalid token") from exc

        identity = await self._repository.get_authenticated_identity(
            user_id=user_id,
            organization_id=organization_id,
            membership_id=membership_id,
            session_id=session_id,
            token_hash=hash_token(token),
        )
        if identity is None:
            raise AuthenticationError("Session is invalid or revoked")
        return AuthenticatedIdentity(
            user_id=identity.user.id,
            email=identity.user.email,
            organization_id=identity.organization.id,
            organization_name=identity.organization.name,
            membership_id=identity.membership.id,
            role=identity.membership.role.name,
            permissions=frozenset(
                permission.code for permission in identity.membership.role.permissions
            ),
            session_id=session_id,
        )

    async def logout(self, identity: AuthenticatedIdentity) -> None:
        await self._repository.revoke_session(identity.session_id)
        self._repository.add_audit_event(
            AuditEvent(
                organization_id=identity.organization_id,
                actor_id=identity.user_id,
                action="identity.logout",
                resource_type="auth_session",
                resource_id=str(identity.session_id),
                result="success",
            )
        )
        await self._repository.commit()
