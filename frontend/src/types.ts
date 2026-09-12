export type Sport = "nfl" | "nba";

export type MarketType =
  | "moneyline"
  | "spread"
  | "alternate_spread"
  | "total"
  | "player_points"
  | "player_rebounds"
  | "player_assists"
  | "player_threes"
  | "player_points_rebounds_assists"
  | "player_passing_yards"
  | "player_rushing_yards"
  | "player_receiving_yards"
  | "player_passing_rushing_yards"
  | "player_anytime_touchdown";

const PLAYER_PROP_MARKETS: ReadonlySet<MarketType> = new Set([
  "player_points",
  "player_rebounds",
  "player_assists",
  "player_threes",
  "player_points_rebounds_assists",
  "player_passing_yards",
  "player_rushing_yards",
  "player_receiving_yards",
  "player_passing_rushing_yards",
  "player_anytime_touchdown",
]);

export function isPlayerPropMarket(market: MarketType): boolean {
  return PLAYER_PROP_MARKETS.has(market);
}

export type OfferStatus = "available" | "missing" | "suspended" | "stale";

export interface Event {
  id: string;
  sport: Sport;
  league: string;
  home_team: string;
  away_team: string;
  start_time: string;
}

export interface Offer {
  event_id: string;
  provider: string;
  bookmaker: string;
  market_type: MarketType;
  selection: string;
  line: number | null;
  price_american: number | null;
  price_decimal: number | null;
  player_name: string | null;
  provider_offer_id: string | null;
  provider_updated_at: string | null;
  observed_at: string;
  deep_link: string | null;
  status: OfferStatus;
}

export interface EventComparison {
  event: Event;
  offers: Offer[];
}

export interface ProviderDetails {
  status: string;
  cache_hit: boolean;
  stale: boolean;
  last_refreshed_at: string | null;
  error_type: string | null;
  quota_remaining: number | null;
}

export interface ComparisonResponse {
  generated_at: string;
  provider_status: Record<string, string>;
  provider_details: Record<string, ProviderDetails>;
  events: EventComparison[];
}
