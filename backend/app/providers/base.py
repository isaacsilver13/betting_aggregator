from collections.abc import Sequence
from typing import Optional, Protocol

from app.domain.models import EventComparison, MarketType, Sport


class OddsProvider(Protocol):
    name: str
    status: str

    async def get_comparisons(
        self,
        sport: Optional[Sport] = None,
        event_id: Optional[str] = None,
        market_type: Optional[MarketType] = None,
        force_refresh: bool = False,
    ) -> Sequence[EventComparison]:
        ...
