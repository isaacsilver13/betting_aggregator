import asyncio
from typing import Any, Optional

import httpx

from app.domain.models import MarketType, Sport
from app.providers.errors import (
    ProviderAuthError,
    ProviderPayloadError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUpstreamError,
)

# Core markets available for all sports
CORE_MARKETS = ("h2h", "spreads", "totals")

# Map sports to their available markets
SPORT_MARKETS = {
    "NFL": CORE_MARKETS,
    "NBA": CORE_MARKETS,
}


class TheOddsApiClient:
    base_url = "https://api.the-odds-api.com/v4"

    def __init__(
        self,
        api_key: str,
        timeout: float = 15.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.transport = transport
        self.quota_remaining: Optional[int] = None

    async def fetch_odds(self, sport: Sport) -> list[dict[str, Any]]:
        sport_name = sport.value.upper()  # Convert Sport enum to string like "NFL", "NBA"
        markets = SPORT_MARKETS.get(sport_name, CORE_MARKETS)
        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": ",".join(markets),
            "oddsFormat": "american",
        }
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    transport=self.transport,
                ) as client:
                    response = await client.get(f"/sports/{sport_key(sport)}/odds", params=params)
                    self.quota_remaining = _quota_remaining(response)
                    if response.status_code in {401, 403}:
                        raise ProviderAuthError("The Odds API rejected the configured credentials")
                    if response.status_code == 429:
                        raise ProviderRateLimitError("The Odds API rate limit was reached")
                    if response.status_code >= 500:
                        raise ProviderUpstreamError(
                            f"The Odds API returned upstream status {response.status_code}"
                        )
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, list):
                        raise ProviderPayloadError("The Odds API returned a non-list payload")
                    return payload
            except (ProviderAuthError, ProviderRateLimitError, ProviderPayloadError):
                raise
            except httpx.TimeoutException as error:
                if attempt >= self.max_retries:
                    raise ProviderTimeoutError("The Odds API request timed out") from error
            except (httpx.HTTPError, ProviderUpstreamError) as error:
                if attempt >= self.max_retries:
                    if isinstance(error, ProviderUpstreamError):
                        raise
                    raise ProviderUpstreamError("The Odds API request failed") from error

            await asyncio.sleep(self.backoff_seconds * (2**attempt))

        raise ProviderUpstreamError("The Odds API request exhausted its retry budget")


def _quota_remaining(response: httpx.Response) -> Optional[int]:
    value = response.headers.get("x-requests-remaining")
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def sport_key(sport: Sport) -> str:
    return {
        Sport.NFL: "americanfootball_nfl",
        Sport.NBA: "basketball_nba",
    }[sport]


def market_type_for_key(market_key: str) -> Optional[MarketType]:
    return {
        "h2h": MarketType.MONEYLINE,
        "spreads": MarketType.SPREAD,
        "totals": MarketType.TOTAL,
        "alternate_spreads": MarketType.ALTERNATE_SPREAD,
        "alternate_totals": MarketType.TOTAL,
        "player_points": MarketType.PLAYER_POINTS,
        "player_rebounds": MarketType.PLAYER_REBOUNDS,
        "player_assists": MarketType.PLAYER_ASSISTS,
        "player_threes": MarketType.PLAYER_THREES,
        "player_pass_yds": MarketType.PLAYER_PASSING_YARDS,
        "player_rush_yds": MarketType.PLAYER_RUSHING_YARDS,
        "player_reception_yds": MarketType.PLAYER_RECEIVING_YARDS,
        "player_anytime_td": MarketType.PLAYER_ANYTIME_TOUCHDOWN,
    }.get(market_key)


