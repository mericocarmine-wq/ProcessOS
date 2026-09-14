from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from urllib.parse import urlencode
from uuid import UUID, uuid4

from app.core.exceptions import ProcessOSError
from app.core.persistence.auth_repository import SqlAlchemyAuthRepository
from app.core.persistence.models import (
    AuditEvent,
    AuthSession,
    Organization,
    PasswordResetToken,
    User,
)
from app.core.ports import PasswordResetDelivery
from app.core.security import (
    InvalidTokenError,
    TokenService,
    hash_password,
    hash_token,
    verify_password,
)

_LOCAL_RESET_URL = "http://localhost:3001/reset-password"


class AuthenticationError(ProcessOSError):
    pass


class AccountConflictError(ProcessOSError):
    pass


class RecoveryUnavailableError(ProcessOSError):
    pass


class InvalidRecoveryTokenError(ProcessOSError):
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
    def __init__(
        self,
        repository: SqlAlchemyAuthRepository,
        tokens: TokenService,
        recovery_delivery: PasswordResetDelivery | None = None,
        password_reset_minutes: int = 30,
        password_reset_base_url: str | None = None,
    ) -> None:
        self._repository = repository
        self._tokens = tokens
        self._recovery_delivery = recovery_delivery
        self._password_reset_minutes = password_reset_minutes
        self._password_reset_base_url = password_reset_base_url or _LOCAL_RESET_URL

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

    async def request_password_reset(self, email: str) -> None:
        if self._recovery_delivery is None:
            raise RecoveryUnavailableError("Password recovery is not configured")
        user = await self._repository.find_user_by_email(email)
        if user is None:
            return
        raw_token = token_urlsafe(32)
        await self._repository.invalidate_password_resets(user.id)
        self._repository.add_password_reset(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=self._password_reset_minutes),
            )
        )
        await self._repository.commit()
        reset_url = f"{self._password_reset_base_url}?{urlencode({'token': raw_token})}"
        await self._recovery_delivery.send(email=user.email, reset_url=reset_url)

    async def reset_password(self, token: str, new_password: str) -> None:
        consumed = await self._repository.consume_password_reset(
            hash_token(token), hash_password(new_password)
        )
        if not consumed:
            raise InvalidRecoveryTokenError("Reset token is invalid or expired")
        await self._repository.commit()
