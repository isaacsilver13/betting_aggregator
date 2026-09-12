import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.domain.models import Event, EventComparison, Offer, Sport
from app.identity import canonical_event_id, canonical_player_name, canonicalize_comparison
from app.providers.registry import ProviderRegistry


def make_event(home_team: str, away_team: str, start_time: datetime) -> Event:
    return Event(
        id="provider:event",
        sport=Sport.NFL,
        league="American Football NFL",
        home_team=home_team,
        away_team=away_team,
        start_time=start_time,
    )


def test_event_identity_matches_aliases_and_nearby_provider_timestamps() -> None:
    start = datetime(2026, 9, 10, 19, 2, tzinfo=timezone.utc)
    first = make_event("NY Giants", "SF 49ers", start)
    second = make_event("New York Giants", "San Francisco 49ers", start + timedelta(minutes=2))

    assert canonical_event_id(first) == canonical_event_id(second)


def test_player_identity_is_separate_and_reviewable() -> None:
    assert canonical_player_name("  Quarterback-One ") == "quarterback one"


def test_canonicalize_comparison_rewrites_offer_event_ids() -> None:
    comparison = EventComparison(
        event=make_event("Home Hawks", "Away Comets", datetime.now(timezone.utc)),
        offers=[
            Offer(
                event_id="provider:event",
                provider="fixture",
                bookmaker="DraftKings",
                market_type="moneyline",
                selection="Home Hawks",
                price_american=-110,
                price_decimal=1.9091,
                observed_at=datetime.now(timezone.utc),
            )
        ],
    )

    normalized = canonicalize_comparison(comparison)

    assert normalized.event.id.startswith("event:")
    assert normalized.offers[0].event_id == normalized.event.id


class FakeProvider:
    status = "configured"

    def __init__(self, name: str, comparison: EventComparison, error: Optional[Exception] = None):
        self.name = name
        self.comparison = comparison
        self.error = error

    async def get_comparisons(self, sport=None):
        if self.error:
            raise self.error
        return [self.comparison]


def test_registry_merges_same_event_and_isolates_provider_failure() -> None:
    start = datetime(2026, 9, 10, 19, 2, tzinfo=timezone.utc)
    first = EventComparison(
        event=make_event("NY Giants", "SF 49ers", start),
        offers=[],
    )
    second = EventComparison(
        event=make_event("New York Giants", "San Francisco 49ers", start + timedelta(minutes=1)),
        offers=[],
    )
    registry = ProviderRegistry(
        [
            FakeProvider("provider_one", first),
            FakeProvider("provider_two", second),
            FakeProvider("provider_down", second, RuntimeError("offline")),
        ]
    )

    comparisons = asyncio.run(registry.get_comparisons(Sport.NFL))

    assert len(comparisons) == 1
    assert registry.status == "partial"
    assert registry.provider_errors == {"provider_down": "RuntimeError"}