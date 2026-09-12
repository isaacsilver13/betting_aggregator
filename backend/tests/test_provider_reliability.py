import asyncio
from typing import Optional

import httpx
import pytest
from app.domain.models import EventComparison, Sport
from app.providers.cache import CachedOddsProvider
from app.providers.errors import ProviderAuthError, ProviderRateLimitError, ProviderTimeoutError
from app.providers.the_odds_api.client import TheOddsApiClient


class CountingProvider:
    name = "counting"
    status = "configured"

    def __init__(self) -> None:
        self.calls = 0
        self.fail = False
        self.quota_remaining: Optional[int] = None

    async def get_comparisons(
        self,
        sport: Optional[Sport] = None,
        event_id: Optional[str] = None,
        market_type=None,
        force_refresh: bool = False,
    ) -> list[EventComparison]:
        self.calls += 1
        if self.fail:
            raise TimeoutError("fixture failure")
        return []


def test_cache_coalesces_concurrent_refreshes() -> None:
    async def scenario() -> None:
        inner = CountingProvider()
        provider = CachedOddsProvider(inner, ttl_seconds=60)

        await asyncio.gather(*[provider.get_comparisons(Sport.NFL) for _ in range(3)])

        assert inner.calls == 1
        assert provider.cache_hit is True

    asyncio.run(scenario())


def test_cache_returns_last_good_snapshot_after_refresh_failure() -> None:
    async def scenario() -> None:
        inner = CountingProvider()
        provider = CachedOddsProvider(inner, ttl_seconds=0)

        await provider.get_comparisons(Sport.NFL)
        inner.fail = True
        await provider.get_comparisons(Sport.NFL)

        assert inner.calls == 2
        assert provider.status == "stale"
        assert provider.last_error_type == "TimeoutError"

    asyncio.run(scenario())


def test_odds_api_client_captures_quota_remaining() -> None:
    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                headers={"x-requests-remaining": "17"},
                json=[],
                request=request,
            )

        client = TheOddsApiClient("test-key", transport=httpx.MockTransport(handler))

        assert await client.fetch_odds(Sport.NFL) == []
        assert client.quota_remaining == 17

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [(401, ProviderAuthError), (429, ProviderRateLimitError)],
)
def test_odds_api_client_maps_non_retryable_provider_errors(status_code, error_type) -> None:
    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code, request=request)

        client = TheOddsApiClient("test-key", transport=httpx.MockTransport(handler))

        with pytest.raises(error_type):
            await client.fetch_odds(Sport.NFL)

    asyncio.run(scenario())


def test_odds_api_client_maps_timeout_after_retry_budget() -> None:
    async def scenario() -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            raise httpx.ReadTimeout("timed out", request=request)

        client = TheOddsApiClient(
            "test-key",
            max_retries=1,
            backoff_seconds=0,
            transport=httpx.MockTransport(handler),
        )

        with pytest.raises(ProviderTimeoutError):
            await client.fetch_odds(Sport.NFL)
        assert calls == 2

    asyncio.run(scenario())


def test_cache_suppresses_refresh_when_quota_is_at_threshold() -> None:
    async def scenario() -> None:
        inner = CountingProvider()
        provider = CachedOddsProvider(inner, ttl_seconds=0, min_quota_remaining=5)

        await provider.get_comparisons(Sport.NFL)
        inner.quota_remaining = 5
        await provider.get_comparisons(Sport.NFL)

        assert inner.calls == 1
        assert provider.last_error_type == "quota_low"
        assert provider.status == "stale"

    asyncio.run(scenario())


def test_cache_force_refresh_bypasses_warm_snapshot() -> None:
    async def scenario() -> None:
        inner = CountingProvider()
        provider = CachedOddsProvider(inner, ttl_seconds=60)

        await provider.get_comparisons(Sport.NFL)
        await provider.get_comparisons(Sport.NFL, force_refresh=True)

        assert inner.calls == 2

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("sport", "expected_path"),
    [
        (Sport.NFL, "/v4/sports/americanfootball_nfl/odds"),
        (Sport.NBA, "/v4/sports/basketball_nba/odds"),
    ],
)
def test_odds_api_client_requests_main_and_alternate_markets(
    sport: Sport, expected_path: str
) -> None:
    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == expected_path
            requested_markets = set(request.url.params["markets"].split(","))
            assert {"h2h", "spreads", "totals", "alternate_spreads"}.issubset(
                requested_markets
            )
            return httpx.Response(200, json=[], request=request)

        client = TheOddsApiClient("test-key", transport=httpx.MockTransport(handler))

        assert await client.fetch_odds(sport) == []

    asyncio.run(scenario())