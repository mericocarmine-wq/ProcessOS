import asyncio
import socket
from urllib.parse import urlparse

import httpx

from app.commercial.domain.discovery import is_public_address
from app.commercial.domain.research import FetchedPage

MAX_RESPONSE_BYTES = 1_000_000


class UnsafeResearchUrlError(ValueError):
    pass


class SafeWebsiteFetcher:
    def __init__(self, timeout_seconds: float = 8.0, retries: int = 1) -> None:
        self._timeout = timeout_seconds
        self._retries = retries

    async def _validate(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise UnsafeResearchUrlError("Only public HTTP(S) URLs are allowed")
        addresses = await asyncio.to_thread(
            socket.getaddrinfo, parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM
        )
        if not addresses or any(not is_public_address(str(item[4][0])) for item in addresses):
            raise UnsafeResearchUrlError("Private or reserved network targets are blocked")

    async def fetch(self, url: str) -> FetchedPage:
        await self._validate(url)
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout,
                    follow_redirects=False,
                    headers={"User-Agent": "ProcessOS-Research/1.0"},
                ) as client:
                    async with client.stream("GET", url) as response:
                        response.raise_for_status()
                        content_type = response.headers.get("content-type", "")
                        if "text/html" not in content_type:
                            raise ValueError("Research target is not HTML")
                        payload = bytearray()
                        async for chunk in response.aiter_bytes():
                            payload.extend(chunk)
                            if len(payload) > MAX_RESPONSE_BYTES:
                                raise ValueError("Research response exceeds size limit")
                        return FetchedPage(str(response.url), payload.decode(errors="replace"))
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < self._retries:
                    await asyncio.sleep(0.2)
        raise RuntimeError("Website research failed") from last_error
