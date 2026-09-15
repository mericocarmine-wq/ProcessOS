import asyncio
from functools import partial

import httpx
import pytest

from app.commercial.infrastructure.overpass import (
    DiscoveryProviderError,
    OverpassDiscoveryProvider,
    _cache,
)


@pytest.fixture(autouse=True)
def isolated_cache() -> None:
    _cache.clear()


def mock_http(monkeypatch: pytest.MonkeyPatch, handler: object) -> None:
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        partial(
            httpx.AsyncClient,
            transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
        ),
    )


async def test_search_resolves_city_then_bounds_and_preserves_contacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queries = []

    def handle(request: httpx.Request) -> httpx.Response:
        query = request.url.params["data"]
        queries.append(query)
        assert request.headers["user-agent"] == "ProcessOS/1.0"
        if '"place"' in query:
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {"lat": 40.416782, "lon": -3.703507, "tags": {"place": "city"}},
                        {"lat": 4.7, "lon": -74.2, "tags": {"place": "town"}},
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "elements": [
                    {
                        "type": "node",
                        "id": 42,
                        "tags": {
                            "name": "Constructor",
                            "contact:phone": "+34 910000000",
                            "contact:email": "info@example.com",
                            "contact:website": "https://example.com",
                        },
                    },
                ]
            },
        )

    mock_http(monkeypatch, handle)
    provider = OverpassDiscoveryProvider()
    records = await provider.search("construction", 'Madrid"', 5)
    assert len(queries) == 2 and 'Madrid\\"' in queries[0]
    assert "area" not in queries[1] and "40.371866" in queries[1]
    assert records[0].phone == "+34 910000000"
    assert records[0].email == "info@example.com"
    assert records[0].source_url == "https://www.openstreetmap.org/node/42"
    assert await provider.search("construction", 'Madrid"', 5) == records
    assert len(queries) == 2  # Cache survives new request-scoped provider instances too.
    await OverpassDiscoveryProvider().search("construction", 'Madrid"', 5)
    assert len(queries) == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"elements": [], "remark": "runtime error: Query timed out"},
        {},
        {"elements": None},
        [],
    ],
)
async def test_http_200_errors_are_not_empty_success_or_cached(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
) -> None:
    mock_http(monkeypatch, lambda request: httpx.Response(200, json=payload))
    with pytest.raises(DiscoveryProviderError):
        await OverpassDiscoveryProvider().search("construction", "40.4,-3.7", 5)
    assert not _cache


async def test_sequential_fallback_and_valid_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    hosts = []

    def handle(request: httpx.Request) -> httpx.Response:
        hosts.append(request.url.host)
        return (
            httpx.Response(503) if len(hosts) == 1 else httpx.Response(200, json={"elements": []})
        )

    mock_http(monkeypatch, handle)
    assert await OverpassDiscoveryProvider().search("construction", "40.4,-3.7", 5) == []
    assert hosts == ["overpass-api.de", "overpass.private.coffee"]


@pytest.mark.parametrize(
    "elements",
    [
        [],
        [
            {"lat": 40, "lon": -3, "tags": {"place": "city"}},
            {"lat": 41, "lon": -4, "tags": {"place": "city"}},
        ],
    ],
)
async def test_missing_or_ambiguous_city_never_imports(
    monkeypatch: pytest.MonkeyPatch,
    elements: list[object],
) -> None:
    mock_http(monkeypatch, lambda request: httpx.Response(200, json={"elements": elements}))
    with pytest.raises(ValueError):
        await OverpassDiscoveryProvider().search("construction", "Example", 5)


@pytest.mark.parametrize("city", ["nan,0", "0,inf", "91,0", "0,180", "Madrid,España"])
async def test_invalid_coordinates(city: str) -> None:
    with pytest.raises(ValueError):
        await OverpassDiscoveryProvider().search("construction", city, 5)


async def test_total_deadline_cancels_pending_request(monkeypatch: pytest.MonkeyPatch) -> None:
    cancelled = False

    async def slow(self: OverpassDiscoveryProvider, endpoint: str, query: str) -> dict[str, object]:
        nonlocal cancelled
        try:
            await asyncio.sleep(1)
        finally:
            cancelled = True
        return {"elements": []}

    monkeypatch.setattr(OverpassDiscoveryProvider, "_fetch_endpoint", slow)
    with pytest.raises(DiscoveryProviderError):
        await OverpassDiscoveryProvider(total_timeout_seconds=0.01).search(
            "construction",
            "40.4,-3.7",
            5,
        )
    assert cancelled
