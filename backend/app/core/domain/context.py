from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OrganizationContext:
    """Trusted tenant scope resolved by the backend from authenticated identity."""

    organization_id: UUID
    actor_id: UUID

