from collections.abc import Sequence
from typing import Optional

from app.domain.models import EventComparison, MarketType, Sport


class EmptyOddsProvider:
    name = "unconfigured"
    status = "not_configured"

    async def get_comparisons(
        self,
        sport: Optional[Sport] = None,
        event_id: Optional[str] = None,
        market_type: Optional[MarketType] = None,
        force_refresh: bool = False,
    ) -> Sequence[EventComparison]:
        return []
