import hashlib
import re
import unicodedata
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Optional

from app.domain.models import Event, EventComparison, MarketType

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")

# Keep aliases explicit and reviewable. Provider-specific aliases can be added
# here after comparing real payloads rather than inferred silently.
TEAM_ALIASES: Mapping[str, str] = {
    "ny giants": "new york giants",
    "ny jets": "new york jets",
    "sf 49ers": "san francisco 49ers",
}
PLAYER_ALIASES: Mapping[str, str] = {}


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = _NON_ALPHANUMERIC.sub(" ", normalized.casefold())
    return " ".join(normalized.split())


def canonical_team_name(value: str, aliases: Mapping[str, str] = TEAM_ALIASES) -> str:
    normalized = normalize_name(value)
    return aliases.get(normalized, normalized)


def canonical_player_name(value: str, aliases: Mapping[str, str] = PLAYER_ALIASES) -> str:
    normalized = normalize_name(value)
    return aliases.get(normalized, normalized)


def canonical_event_id(event: Event, time_bucket_minutes: int = 5) -> str:
    bucket = _time_bucket(event.start_time, time_bucket_minutes)
    identity = "|".join(
        (
            event.sport.value,
            normalize_name(event.league),
            canonical_team_name(event.home_team),
            canonical_team_name(event.away_team),
            bucket,
        )
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"event:{digest}"


def canonicalize_comparison(comparison: EventComparison) -> EventComparison:
    event_id = canonical_event_id(comparison.event)
    event = comparison.event.model_copy(update={"id": event_id})
    offers = [offer.model_copy(update={"event_id": event_id}) for offer in comparison.offers]
    return EventComparison(event=event, offers=offers)


def scope_comparisons(
    comparisons: list[EventComparison],
    event_id: Optional[str] = None,
    market_type: Optional[MarketType] = None,
) -> list[EventComparison]:
    scoped: list[EventComparison] = []
    for comparison in comparisons:
        if event_id is not None and comparison.event.id != event_id:
            continue
        offers = comparison.offers
        if market_type is not None:
            offers = [offer for offer in offers if offer.market_type is market_type]
        scoped.append(EventComparison(event=comparison.event, offers=offers))
    return scoped


def _time_bucket(value: datetime, bucket_minutes: int) -> str:
    if bucket_minutes <= 0:
        raise ValueError("time_bucket_minutes must be positive")
    utc_value = value.astimezone(timezone.utc)
    total_minutes = utc_value.hour * 60 + utc_value.minute
    bucketed_minutes = total_minutes - total_minutes % bucket_minutes
    return utc_value.replace(
        hour=bucketed_minutes // 60,
        minute=bucketed_minutes % 60,
        second=0,
        microsecond=0,
    ).isoformat()