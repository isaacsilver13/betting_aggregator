from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import ProviderMode, Settings, load_settings
from app.domain.models import (
    ComparisonResponse,
    HistoryResponse,
    MarketType,
    ProviderDetails,
    Sport,
)
from app.identity import canonicalize_comparison, scope_comparisons
from app.providers.base import OddsProvider
from app.providers.cache import CachedOddsProvider
from app.providers.errors import OddsProviderError
from app.providers.fixture import FixtureOddsProvider
from app.providers.stub import EmptyOddsProvider
from app.providers.the_odds_api import TheOddsApiProvider
from app.providers.the_odds_api.client import TheOddsApiClient
from app.storage.database import create_engine, create_session_factory
from app.storage.repository import OddsRepository

router = APIRouter(prefix="/api/v1")


def build_provider(settings: Optional[Settings] = None) -> OddsProvider:
    active_settings = settings or load_settings()
    if active_settings.the_odds_api_key:
        if active_settings.provider_mode is not ProviderMode.LIVE:
            raise RuntimeError("THE_ODDS_API_KEY requires PROVIDER_MODE=live")
        return TheOddsApiProvider(
            TheOddsApiClient(
                active_settings.the_odds_api_key,
                timeout=active_settings.provider_timeout_seconds,
            )
        )
    if active_settings.odds_provider == "fixture":
        if active_settings.provider_mode is ProviderMode.LIVE:
            raise RuntimeError("ODDS_PROVIDER=fixture requires PROVIDER_MODE=fixture")
        return FixtureOddsProvider()
    if not active_settings.the_odds_api_key:
        if active_settings.provider_mode is ProviderMode.LIVE:
            return EmptyOddsProvider()
        if active_settings.odds_provider == "fixture":
            return FixtureOddsProvider()
        return EmptyOddsProvider()

    return EmptyOddsProvider()


settings = load_settings()
provider: OddsProvider = CachedOddsProvider(
    build_provider(settings),
    ttl_seconds=settings.cache_ttl_seconds,
    min_quota_remaining=settings.provider_min_quota_remaining,
)
repository = None
if settings.persistence_enabled:
    repository = OddsRepository(create_session_factory(create_engine(settings)))


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/status")
async def status() -> dict[str, object]:
    provider_status = provider.status
    return {
        "status": "unconfigured" if provider_status == "not_configured" else "ok",
        "provider": provider.name,
        "provider_status": provider_status,
        "data_stale": provider_status == "stale",
        "generated_at": getattr(provider, "last_refreshed_at", None),
        "event_count": getattr(provider, "cached_event_count", 0),
    }


@router.get("/odds", response_model=ComparisonResponse)
async def get_odds(
    sport: Optional[Sport] = Query(default=None),
    event_id: Optional[str] = Query(default=None, min_length=1),
    market_type: Optional[MarketType] = Query(default=None),
    force_refresh: bool = Query(default=False),
    include_props: bool = Query(
        default=False,
        description=(
            "Also fetch player-prop offers. Costs one extra provider request "
            "per event, so only set this when the UI is actually showing a "
            "player-prop market."
        ),
    ),
) -> ComparisonResponse:
    started_at = datetime.now(timezone.utc)
    provider_error: Optional[OddsProviderError] = None
    try:
        comparisons = await provider.get_comparisons(
            sport=sport,
            event_id=event_id,
            market_type=market_type,
            force_refresh=force_refresh,
            include_player_props=include_props,
        )
    except OddsProviderError as error:
        provider_error = error
        comparisons = []
    comparisons = scope_comparisons(
        [canonicalize_comparison(comparison) for comparison in comparisons],
        event_id,
        market_type,
    )
    completed_at = datetime.now(timezone.utc)
    if repository is not None:
        if provider_error is None:
            await repository.record_comparisons(
                provider=provider.name,
                comparisons=comparisons,
                started_at=started_at,
                completed_at=completed_at,
                sport=sport,
            )
        else:
            await repository.record_refresh_failure(
                provider=provider.name,
                started_at=started_at,
                completed_at=completed_at,
                error_type=provider_error.error_type,
                error_message=str(provider_error),
                sport=sport,
                quota_remaining=getattr(provider, "quota_remaining", None),
            )
        await repository.prune_expired(settings.observation_retention_days, completed_at)
    return ComparisonResponse(
        generated_at=completed_at,
        provider_status={provider.name: "error" if provider_error else provider.status},
        provider_details={
            provider.name: ProviderDetails(
                status="error" if provider_error else provider.status,
                cache_hit=bool(getattr(provider, "cache_hit", False)),
                stale=provider.status == "stale",
                last_refreshed_at=getattr(provider, "last_refreshed_at", None),
                error_type=(
                    provider_error.error_type
                    if provider_error
                    else getattr(provider, "last_error_type", None)
                ),
                quota_remaining=getattr(provider, "quota_remaining", None),
            )
        },
        events=list(comparisons),
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    event_id: str = Query(min_length=1),
    market_type: Optional[MarketType] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
) -> HistoryResponse:
    if repository is None:
        raise HTTPException(status_code=503, detail="Persistence is disabled")
    offers = await repository.get_history(
        event_id=event_id,
        market_type=market_type,
        limit=limit,
    )
    return HistoryResponse(event_id=event_id, offers=offers)
