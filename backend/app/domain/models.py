from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Sport(str, Enum):
    NFL = "nfl"
    NBA = "nba"


class MarketType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    ALTERNATE_SPREAD = "alternate_spread"
    TOTAL = "total"
    PLAYER_POINTS = "player_points"
    PLAYER_REBOUNDS = "player_rebounds"
    PLAYER_ASSISTS = "player_assists"
    PLAYER_THREES = "player_threes"
    PLAYER_PASSING_YARDS = "player_passing_yards"
    PLAYER_RUSHING_YARDS = "player_rushing_yards"
    PLAYER_RECEIVING_YARDS = "player_receiving_yards"
    PLAYER_ANYTIME_TOUCHDOWN = "player_anytime_touchdown"


class OfferStatus(str, Enum):
    AVAILABLE = "available"
    MISSING = "missing"
    SUSPENDED = "suspended"
    STALE = "stale"


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    sport: Sport
    league: str
    home_team: str
    away_team: str
    start_time: datetime


class Offer(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    provider: str
    bookmaker: str
    market_type: MarketType
    selection: str
    line: Optional[float] = None
    price_american: Optional[int] = Field(default=None, ge=-10000, le=10000)
    price_decimal: Optional[float] = Field(default=None, gt=1.0)
    player_name: Optional[str] = None
    provider_offer_id: Optional[str] = None
    provider_updated_at: Optional[datetime] = None
    observed_at: datetime
    deep_link: Optional[str] = None
    status: OfferStatus = OfferStatus.AVAILABLE


class EventComparison(BaseModel):
    event: Event
    offers: list[Offer] = Field(default_factory=list)


class ProviderDetails(BaseModel):
    status: str
    cache_hit: bool = False
    stale: bool = False
    last_refreshed_at: Optional[datetime] = None
    error_type: Optional[str] = None
    quota_remaining: Optional[int] = None


class ComparisonResponse(BaseModel):
    generated_at: datetime
    provider_status: dict[str, str]
    provider_details: dict[str, ProviderDetails] = Field(default_factory=dict)
    events: list[EventComparison] = Field(default_factory=list)


class HistoryResponse(BaseModel):
    event_id: str
    offers: list[Offer] = Field(default_factory=list)
