import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from app.domain.models import MarketType, Sport
from app.providers.the_odds_api.adapter import TheOddsApiProvider, american_to_decimal

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "the_odds_api_nfl.json"


class FakeTheOddsApiClient:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self.payload = payload
        self.requested_sports: list[Sport] = []

    async def fetch_odds(self, sport: Sport) -> list[dict[str, Any]]:
        self.requested_sports.append(sport)
        return self.payload


def test_normalizes_events_main_markets_and_props() -> None:
    payload = json.loads(FIXTURE_PATH.read_text())
    client = FakeTheOddsApiClient(payload)
    provider = TheOddsApiProvider(client)

    comparisons = asyncio.run(provider.get_comparisons(Sport.NFL))

    assert client.requested_sports == [Sport.NFL]
    assert len(comparisons) == 1
    comparison = comparisons[0]
    assert comparison.event.id == "the_odds_api:event-nfl-1"
    assert comparison.event.sport is Sport.NFL
    assert comparison.event.home_team == "Home Hawks"

    moneyline = next(
        offer for offer in comparison.offers if offer.market_type is MarketType.MONEYLINE
    )
    assert moneyline.bookmaker == "DraftKings"
    assert moneyline.selection == "Home Hawks"
    assert moneyline.price_american == -120
    assert moneyline.price_decimal == pytest.approx(1.8333)

    alternate_spreads = [
        offer
        for offer in comparison.offers
        if offer.market_type is MarketType.ALTERNATE_SPREAD
    ]
    assert {offer.line for offer in alternate_spreads} == {-4.5, -1.5, 1.5, 4.5}
    assert all(
        offer.provider_offer_id and "alternate_spreads" in offer.provider_offer_id
        for offer in alternate_spreads
    )
    assert all(offer.market_type is not MarketType.SPREAD for offer in alternate_spreads)

    passing = next(
        offer for offer in comparison.offers if offer.market_type is MarketType.PLAYER_PASSING_YARDS
    )
    assert passing.player_name == "Quarterback One"
    assert passing.selection == "Over"
    assert passing.line == 245.5
    assert passing.provider_updated_at is not None

    assert all(offer.selection != "Ignore me" for offer in comparison.offers)


def test_american_to_decimal_handles_positive_and_negative_prices() -> None:
    assert american_to_decimal(150) == 2.5
    assert american_to_decimal(-200) == 1.5
