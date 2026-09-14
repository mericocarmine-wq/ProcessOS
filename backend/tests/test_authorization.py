from uuid import uuid4

import pytest

from app.core.application.apps import AppLauncherService, AuthorizationError
from app.core.application.auth import AuthenticatedIdentity


class RepositoryThatMustNotBeCalled:
    async def set_enabled(self, code: str, enabled: bool) -> bool:
        raise AssertionError("Repository must not be called after authorization denial")


async def test_user_without_manage_permission_cannot_change_apps() -> None:
    identity = AuthenticatedIdentity(
        user_id=uuid4(),
        email="viewer@example.com",
        organization_id=uuid4(),
        organization_name="Tenant A",
        membership_id=uuid4(),
        role="viewer",
        permissions=frozenset({"apps.read"}),
        session_id=uuid4(),
    )
    service = AppLauncherService(RepositoryThatMustNotBeCalled(), identity)  # type: ignore[arg-type]

    with pytest.raises(AuthorizationError):
        await service.set_enabled("finance", True)
