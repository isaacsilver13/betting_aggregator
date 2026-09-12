from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.domain.models import Event, EventComparison, MarketType, Offer, Sport


class FixtureOddsProvider:
    name = "fixture"
    status = "configured"

    async def get_comparisons(
        self,
        sport: Optional[Sport] = None,
        event_id: Optional[str] = None,
        market_type: Optional[MarketType] = None,
        force_refresh: bool = False,
    ) -> Sequence[EventComparison]:
        requested_sport = sport or Sport.NFL
        observed_at = datetime.now(timezone.utc)
        event_id = f"{self.name}:{requested_sport.value}:sample"
        event = Event(
            id=event_id,
            sport=requested_sport,
            league="NFL" if requested_sport is Sport.NFL else "NBA",
            home_team="Home Hawks",
            away_team="Away Comets",
            start_time=observed_at + timedelta(hours=2),
        )
        offers = [
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="DraftKings",
                market_type=MarketType.MONEYLINE,
                selection=event.home_team,
                price_american=-120,
                price_decimal=1.8333,
                observed_at=observed_at,
                deep_link="https://sportsbook.draftkings.com/",
            ),
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="DraftKings",
                market_type=MarketType.SPREAD,
                selection=event.home_team,
                line=-2.5,
                price_american=-110,
                price_decimal=1.9091,
                observed_at=observed_at,
            ),
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="DraftKings",
                market_type=MarketType.ALTERNATE_SPREAD,
                selection=event.home_team,
                line=-1.5,
                price_american=-155,
                price_decimal=1.6452,
                observed_at=observed_at,
            ),
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="DraftKings",
                market_type=MarketType.ALTERNATE_SPREAD,
                selection=event.away_team,
                line=1.5,
                price_american=135,
                price_decimal=2.35,
                observed_at=observed_at,
            ),
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="DraftKings",
                market_type=MarketType.TOTAL,
                selection="Over",
                line=44.5,
                price_american=-110,
                price_decimal=1.9091,
                observed_at=observed_at,
            ),
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="DraftKings",
                market_type=MarketType.TOTAL,
                selection="Under",
                line=44.5,
                price_american=-110,
                price_decimal=1.9091,
                observed_at=observed_at,
            ),
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="FanDuel",
                market_type=MarketType.MONEYLINE,
                selection=event.home_team,
                price_american=-115,
                price_decimal=1.8696,
                observed_at=observed_at,
                deep_link="https://sportsbook.fanduel.com/",
            ),
            Offer(
                event_id=event_id,
                provider=self.name,
                bookmaker="FanDuel",
                market_type=MarketType.MONEYLINE,
                selection=event.away_team,
                price_american=105,
                price_decimal=2.05,
                observed_at=observed_at,
                deep_link="https://sportsbook.fanduel.com/",
            ),
        ]
        return [EventComparison(event=event, offers=offers)]