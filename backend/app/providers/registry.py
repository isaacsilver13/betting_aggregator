import asyncio
from collections.abc import Sequence
from typing import Optional

from app.domain.models import EventComparison, MarketType, Sport
from app.identity import canonicalize_comparison, scope_comparisons
from app.providers.base import OddsProvider


class ProviderRegistry:
    name = "aggregated"

    def __init__(self, providers: Sequence[OddsProvider]) -> None:
        self.providers = tuple(providers)
        self.provider_errors: dict[str, str] = {}

    @property
    def status(self) -> str:
        if not self.providers:
            return "not_configured"
        if self.provider_errors and self.provider_errors.keys() == {
            provider.name for provider in self.providers
        }:
            return "error"
        if self.provider_errors:
            return "partial"
        return "configured"

    @property
    def provider_statuses(self) -> dict[str, str]:
        statuses = {provider.name: provider.status for provider in self.providers}
        statuses.update({name: "error" for name in self.provider_errors})
        return statuses

    async def get_comparisons(
        self,
        sport: Optional[Sport] = None,
        event_id: Optional[str] = None,
        market_type: Optional[MarketType] = None,
        force_refresh: bool = False,
    ) -> Sequence[EventComparison]:
        self.provider_errors = {}
        results = await asyncio.gather(
            *(provider.get_comparisons(sport=sport) for provider in self.providers),
            return_exceptions=True,
        )
        merged: dict[str, EventComparison] = {}
        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                self.provider_errors[provider.name] = getattr(
                    result, "error_type", type(result).__name__
                )
                continue
            for comparison in result:
                normalized = canonicalize_comparison(comparison)
                current = merged.get(normalized.event.id)
                if current is None:
                    merged[normalized.event.id] = normalized
                else:
                    merged[normalized.event.id] = EventComparison(
                        event=current.event,
                        offers=[*current.offers, *normalized.offers],
                    )
        return scope_comparisons(list(merged.values()), event_id, market_type)