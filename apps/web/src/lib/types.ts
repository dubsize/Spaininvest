export interface ListingSummary {
  id: number;
  marketplace_code: string;
  external_id: string;
  url: string;
  title: string;
  price_amount: number;
  currency: string;
  price_eur: number;
  city: string | null;
  country: string;
  condition: string;
  image_urls: string[];
  published_at: string | null;
  first_seen_at: string;
  last_seen_at: string;
  status: string;
  price_drop_count: number;
  last_price_change_pct: number | null;
  last_price_change_at: string | null;
  seller_rating: number | null;
  seller_rating_count: number | null;
  normalization_confidence: number;
  variant: Record<string, string>;
  is_demo: boolean;
  source: string;
}

export interface PricePoint {
  price_amount: number;
  currency: string;
  price_eur: number;
  change_type: string;
  change_pct: number | null;
  observed_at: string;
}

export interface ListingDetail extends ListingSummary {
  description: string;
  language: string | null;
  original_price_amount: number | null;
  fx_rate: number;
  fx_timestamp: string | null;
  price_kind: string;
  region: string | null;
  seller_id: string | null;
  seller_name: string | null;
  seller_account_created_at: string | null;
  seller_type: string | null;
  seller_listing_count: number | null;
  condition_raw: string | null;
  category_raw: string | null;
  brand_raw: string | null;
  shipping_available: boolean | null;
  shipping_cost_eur: number | null;
  canonical_product_id: number | null;
  detected_brand: string | null;
  detected_model: string | null;
  variant_key: string;
  accessories: Record<string, boolean>;
  authenticity_info: string | null;
  normalization_method: string | null;
  normalization_details: { reasons?: string[]; candidates?: { slug: string; score: number }[]; accessory_only?: boolean };
  source_metadata: Record<string, unknown>;
  price_history: PricePoint[];
}

export interface RiskFlag { code: string; severity: string; points: number; message: string }

export interface CostLine { label: string; amount: number; side: string; note: string }

export interface Opportunity {
  id: number;
  listing_id: number;
  canonical_product_id: number | null;
  opportunity_type: "FLIP" | "CROSS_BORDER" | "NEGOTIATION" | "NONE";
  resale_country: string;
  source_country: string;
  is_active: boolean;
  status: string;
  purchase_price_eur: number;
  quick_sale_eur: number | null;
  market_value_eur: number | null;
  buy_costs_eur: number;
  sell_costs_eur: number;
  total_costs_eur: number;
  cost_breakdown: { lines?: CostLine[]; route?: string; resale_marketplace?: string; capital?: number; total?: number };
  net_profit_quick_eur: number | null;
  net_profit_market_eur: number | null;
  roi: number | null;
  discount_pct: number | null;
  max_buy_price_eur: number | null;
  target_offer_eur: number | null;
  profit_at_target_offer_eur: number | null;
  expected_holding_days: number | null;
  annualized_roi: number | null;
  profit_velocity: number | null;
  capital_efficiency: number | null;
  profit_per_1000: number | null;
  liquidity_score: number | null;
  liquidity_label: string | null;
  confidence_score: number | null;
  confidence_level: string | null;
  normalization_confidence: number | null;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  risk_score: number;
  risk_flags: RiskFlag[];
  requires_authentication: boolean;
  score: number;
  score_components: Record<string, any>;
  explanation: string[];
  computed_at: string;
  listing: ListingSummary;
  canonical_product: { id: number; slug: string; name: string; brand: string; model: string; category_code: string } | null;
}

export interface Paged<T> { items: T[]; total: number; page: number; page_size: number }

export const DEAL_STATUSES = [
  "DISCOVERED", "WATCHING", "CONTACTED", "NEGOTIATING", "PURCHASED", "RECEIVED",
  "LISTED_FOR_RESALE", "SOLD", "REJECTED", "SCAM_RISK", "EXPIRED",
] as const;
