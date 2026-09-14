from collections.abc import Sequence
from typing import Protocol

from app.core.domain.context import OrganizationContext


class TenantScopedRepository[T](Protocol):
    """Contract for repositories that cannot operate without trusted tenant context."""

    context: OrganizationContext

    async def list(self) -> Sequence[T]: ...
