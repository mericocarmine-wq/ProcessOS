from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import cast
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from pydantic import SecretStr

from app.core.config import Settings

_password_hasher = PasswordHasher()


class InvalidTokenError(ValueError):
    pass


def normalize_allowed_origins(origins: Sequence[object]) -> list[str]:
    """Convert validated URLs to the exact strings expected by CORS middleware."""

    return [str(origin).rstrip("/") for origin in origins]


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password_hash: str, candidate: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, candidate)
    except (InvalidHashError, VerifyMismatchError):
        return False


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


class TokenService:
    def __init__(self, settings: Settings) -> None:
        self._secret: SecretStr = settings.jwt_secret
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._lifetime = timedelta(minutes=settings.access_token_minutes)

    def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        membership_id: UUID,
        session_id: UUID,
        role: str,
    ) -> tuple[str, datetime]:
        now = datetime.now(UTC)
        expires_at = now + self._lifetime
        token = jwt.encode(
            {
                "sub": str(user_id),
                "org": str(organization_id),
                "membership": str(membership_id),
                "sid": str(session_id),
                "role": role,
                "iat": now,
                "exp": expires_at,
                "iss": self._issuer,
                "aud": self._audience,
            },
            self._secret.get_secret_value(),
            algorithm="HS256",
        )
        return token, expires_at

    def decode(self, token: str) -> dict[str, object]:
        try:
            return cast(
                dict[str, object],
                jwt.decode(
                    token,
                    self._secret.get_secret_value(),
                    algorithms=["HS256"],
                    issuer=self._issuer,
                    audience=self._audience,
                    options={"require": ["sub", "org", "membership", "sid", "exp", "iat"]},
                ),
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError("Token validation failed") from exc
