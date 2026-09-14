from typing import Protocol


class PasswordResetDelivery(Protocol):
    async def send(self, *, email: str, reset_url: str) -> None: ...
