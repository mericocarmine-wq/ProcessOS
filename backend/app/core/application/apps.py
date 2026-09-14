from dataclasses import dataclass

from app.core.application.auth import AuthenticatedIdentity
from app.core.exceptions import ProcessOSError
from app.core.persistence.app_repository import SqlAlchemyAppRepository


class AuthorizationError(ProcessOSError):
    pass


class ApplicationNotFoundError(ProcessOSError):
    pass


class CoreApplicationError(ProcessOSError):
    pass


@dataclass(frozen=True, slots=True)
class EnabledApplication:
    code: str
    name: str


class AppLauncherService:
    def __init__(
        self,
        repository: SqlAlchemyAppRepository,
        identity: AuthenticatedIdentity,
    ) -> None:
        self._repository = repository
        self._identity = identity

    def _require(self, permission: str) -> None:
        if permission not in self._identity.permissions:
            raise AuthorizationError(f"Missing permission: {permission}")

    async def list_enabled(self) -> tuple[EnabledApplication, ...]:
        self._require("apps.read")
        apps = await self._repository.list_enabled()
        return tuple(EnabledApplication(code=app.code, name=app.name) for app in apps)

    async def set_enabled(self, code: str, enabled: bool) -> None:
        self._require("apps.manage")
        if code == "core" and not enabled:
            raise CoreApplicationError("ProcessOS Core cannot be disabled")
        changed = await self._repository.set_enabled(code, enabled)
        if not changed:
            raise ApplicationNotFoundError("Application does not exist")
        await self._repository.record_change(
            actor_id=self._identity.user_id,
            app_code=code,
            enabled=enabled,
        )
        await self._repository.commit()
