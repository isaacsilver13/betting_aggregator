import type { ComparisonResponse, MarketType, Sport } from "../types";

interface OddsRequestOptions {
  eventId?: string;
  marketType?: MarketType;
  forceRefresh?: boolean;
  includeProps?: boolean;
}

export async function fetchOdds(
  sport: Sport,
  options: OddsRequestOptions = {},
): Promise<ComparisonResponse> {
  const params = new URLSearchParams({ sport });
  if (options.eventId) params.set("event_id", options.eventId);
  if (options.marketType) params.set("market_type", options.marketType);
  if (options.forceRefresh) params.set("force_refresh", "true");
  if (options.includeProps) params.set("include_props", "true");

  const response = await fetch(`/api/v1/odds?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Odds request failed with status ${response.status}`);
  }

  return response.json() as Promise<ComparisonResponse>;
}
