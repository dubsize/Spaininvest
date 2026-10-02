"use client";
import { use, useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { AlertTriangle, ExternalLink, ShieldAlert } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { ConfidenceBadge, LiquidityBadge, RiskBadge, ScoreBadge, StatusBadge, TypeBadge } from "@/components/badges";
import { PriceHistoryChart, ScoreBars } from "@/components/charts";
import { OfferCalculator, PurchaseDialog, StatusControl } from "@/components/deal-actions";
import { Empty, ErrorBox, KV, Loading } from "@/components/states";
import { Thumb } from "@/components/thumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { apiSend, fetcher } from "@/lib/api";
import { ageFrom, dateTime, eur, flag, humanize, mpLabel, pct } from "@/lib/format";
import type { ListingDetail, ListingSummary, Opportunity } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Resp {
  listing: ListingDetail;
  product: { id: number; name: string; brand: string; category_code: string; slug: string } | null;
  opportunities: Opportunity[];
  comparables: (ListingSummary & { weight: number; kind: string; days_on_market: number | null })[];
}

function OpportunityPanel({ o, onChange }: { o: Opportunity; onChange: () => void }) {
  const negotiation = o.opportunity_type === "NEGOTIATION";
  const lines = o.cost_breakdown?.lines ?? [];
  const vals = o.score_components?.valuation ?? {};
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ScoreBadge score={o.score} />
          <TypeBadge type={o.opportunity_type} />
          <span className="text-xs text-muted-foreground">
            buy {flag(o.source_country)} → resell {flag(o.resale_country)} on {mpLabel(o.cost_breakdown?.resale_marketplace)}
          </span>
        </div>
        <StatusBadge status={o.status} />
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-2">
        <div>
          <KV k="Purchase price" v={eur(o.purchase_price_eur)} />
          <KV k="Estimated quick-sale" v={eur(o.quick_sale_eur)} />
          <KV k="Estimated market value" v={eur(o.market_value_eur)} />
          <KV k="Total costs" v={eur(o.total_costs_eur)} />
          <KV k="Net profit (quick sale)" v={<span className={(o.net_profit_quick_eur ?? 0) > 0 ? "text-pos" : "text-neg"}>{eur(o.net_profit_quick_eur)}</span>} />
          <KV k="Net profit (market price)" v={eur(o.net_profit_market_eur)} />
          <KV k="ROI" v={pct(o.roi)} />
          <KV k="Discount to market" v={pct(o.discount_pct)} />
          <KV k="MAX BUY PRICE" v={<span className="font-semibold">{eur(o.max_buy_price_eur)}</span>} />
          {negotiation && <KV k="Target offer" v={<span className="font-semibold text-warn">{eur(o.target_offer_eur)}</span>} />}
          {negotiation && <KV k="Profit at target offer" v={eur(o.profit_at_target_offer_eur)} />}
          <div className="mt-2 grid grid-cols-2 gap-x-4">
            <KV k="Holding days" v={o.expected_holding_days?.toFixed(0) ?? "—"} />
            <KV k="Annualised ROI" v={o.annualized_roi != null ? pct(o.annualized_roi, 0) : "—"} />
            <KV k="Profit velocity" v={o.profit_velocity != null ? `${eur(o.profit_velocity)}/day` : "—"} />
            <KV k="Profit / €1,000" v={eur(o.profit_per_1000)} />
          </div>
        </div>
        <div className="space-y-3">
          <div>
            <div className="label mb-1">Score breakdown</div>
            <ScoreBars components={o.score_components} />
            {(o.score_components?.caps ?? []).length > 0 && (
              <div className="mt-1 text-2xs text-warn">capped: {(o.score_components.caps as string[]).join(", ")}</div>
            )}
          </div>
          <div className="flex flex-wrap gap-2 text-2xs">
            <span className="flex items-center gap-1">Liquidity <LiquidityBadge label={o.liquidity_label} score={o.liquidity_score} /></span>
            <span className="flex items-center gap-1">Valuation <ConfidenceBadge level={o.confidence_level} n={vals.n} /></span>
            <span className="flex items-center gap-1">Match <span className="num">{pct(o.normalization_confidence, 0)}</span></span>
            <span className="flex items-center gap-1">Risk <RiskBadge level={o.risk_level} /></span>
          </div>
          <div className="text-2xs text-muted-foreground">
            Market value {eur(o.market_value_eur)} · confidence {o.confidence_level} · based on {vals.n ?? 0} comparables ({vals.n_sold ?? 0} sold) · IQR {eur(vals.p25)}–{eur(vals.p75)}
            {(vals.notes ?? []).map((n: string) => (
              <div key={n}>• {n}</div>
            ))}
          </div>
        </div>
        <div>
          <div className="label mb-1">Cost breakdown ({o.cost_breakdown?.route?.replace("_", "-")})</div>
          {lines.length ? (
            lines.map((l, i) => <KV key={i} k={`${l.label}${l.note ? ` (${l.note})` : ""}`} v={eur(l.amount, true)} />)
          ) : (
            <Empty>No costs computed.</Empty>
          )}
        </div>
        <div>
          <div className="label mb-1">Risk assessment — {o.risk_level}</div>
          <ul className="space-y-1">
            {o.risk_flags.length === 0 && <li className="text-xs text-muted-foreground">No risk signals detected.</li>}
            {o.risk_flags.map((f) => (
              <li key={f.code} className={cn("flex gap-1.5 text-xs", f.points > 0 ? (f.severity === "high" ? "text-neg" : f.severity === "medium" ? "text-warn" : "") : "text-pos")}>
                <span>{f.points > 0 ? "•" : "✓"}</span> {f.message}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-2xs text-muted-foreground">Signals only — the scanner never classifies a listing as fraud. Verify before paying.</p>
        </div>
      </CardContent>
      <div className="flex flex-wrap items-center gap-2 border-t p-3">
        <StatusControl opp={o} onChange={onChange} />
        <PurchaseDialog opp={o} onDone={onChange} />
        <OfferCalculator opp={o} />
      </div>
    </Card>
  );
}

export default function ListingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, error, isLoading, mutate } = useSWR<Resp>(`/listings/${id}`, fetcher);
  const { data: products } = useSWR<{ id: number; name: string }[]>("/products", fetcher);
  const [img, setImg] = useState(0);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;
  const l = data.listing;
  const o = data.opportunities;
  const luxury = o.some((x) => x.requires_authentication);
  const nd = l.normalization_details || {};

  async function relink(pid: string) {
    await apiSend("PATCH", `/listings/${l.id}`, { canonical_product_id: pid ? Number(pid) : null });
    mutate();
  }

  return (
    <div className="space-y-3">
      <PageHeader
        title={l.title}
        subtitle={
          <span className="flex flex-wrap items-center gap-2">
            {data.product ? <Link className="text-primary hover:underline" href={`/products/${data.product.id}`}>{data.product.name}</Link> : <span className="text-warn">not matched to a product</span>}
            <span>· {mpLabel(l.marketplace_code)} · {flag(l.country)} {l.city}</span>
            <span>· listed {ageFrom(l.published_at ?? l.first_seen_at)} ago</span>
            {l.is_demo && <span className="rounded bg-warn/20 px-1 text-2xs text-warn">DEMO DATA</span>}
          </span>
        }
        actions={
          <a href={l.url} target="_blank" rel="noopener noreferrer nofollow" className="inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground">
            <ExternalLink className="size-3.5" /> OPEN LISTING
          </a>
        }
      />
      {luxury && (
        <div className="flex items-center gap-2 rounded-md border border-warn/50 bg-warn/10 p-2 text-xs text-warn">
          <ShieldAlert className="size-4" /> Authentication required before purchase. The scanner does not certify authenticity.
        </div>
      )}
      <div className="grid gap-3 xl:grid-cols-[380px_1fr]">
        <div className="space-y-3">
          <Card>
            <CardContent>
              <Thumb src={l.image_urls[img]} title={data.product?.name ?? l.title} size={348} className="!h-56 !w-full" />
              {l.image_urls.length > 1 && (
                <div className="mt-2 flex gap-1 overflow-x-auto">
                  {l.image_urls.map((u, i) => (
                    <button key={u} onClick={() => setImg(i)} className={cn("rounded ring-1", i === img ? "ring-primary" : "ring-transparent")}>
                      <Thumb src={u} title={l.title} size={36} />
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Listing</CardTitle></CardHeader>
            <CardContent>
              <KV k="Asking price" v={`${eur(l.price_eur)}${l.currency !== "EUR" ? ` (${l.price_amount} ${l.currency} @ ${l.fx_rate.toFixed(4)})` : ""}`} />
              {l.original_price_amount && <KV k="Original price" v={eur(l.original_price_amount)} />}
              <KV k="Condition" v={humanize(l.condition)} mono={false} />
              <KV k="Shipping" v={l.shipping_available === false ? "pickup only" : l.shipping_cost_eur != null ? eur(l.shipping_cost_eur, true) : l.shipping_available ? "available" : "unknown"} mono={false} />
              <KV k="Published" v={dateTime(l.published_at)} />
              <KV k="First seen / last seen" v={`${dateTime(l.first_seen_at)} / ${dateTime(l.last_seen_at)}`} />
              <KV k="Status" v={l.status} mono={false} />
              <KV k="Language" v={l.language ?? "—"} />
              <div className="mt-2 max-h-48 overflow-y-auto whitespace-pre-wrap rounded bg-muted/50 p-2 text-xs scroll-thin">{l.description || "(no description)"}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Seller</CardTitle></CardHeader>
            <CardContent>
              <KV k="Name" v={l.seller_name ?? "—"} mono={false} />
              <KV k="Rating" v={l.seller_rating != null ? `${l.seller_rating.toFixed(1)}/5 (${l.seller_rating_count ?? 0} reviews)` : `no rating (${l.seller_rating_count ?? "?"} reviews)`} />
              <KV k="Account age" v={l.seller_account_created_at ? ageFrom(l.seller_account_created_at) : "unknown"} />
              <KV k="Type" v={l.seller_type ?? "unknown"} mono={false} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Normalisation</CardTitle></CardHeader>
            <CardContent>
              <KV k="Product" v={data.product?.name ?? "—"} mono={false} />
              <KV k="Variant" v={Object.entries(l.variant).map(([k, v]) => `${k}: ${v}`).join(", ") || "—"} mono={false} />
              <KV k="Confidence" v={`${pct(l.normalization_confidence, 0)} (${l.normalization_method})`} />
              <KV k="Accessories" v={Object.entries(l.accessories).map(([k, v]) => `${v ? "✓" : "✗"} ${k}`).join("  ") || "—"} mono={false} />
              {l.authenticity_info && <div className="mt-1 text-2xs text-muted-foreground">Seller claims (unverified): “{l.authenticity_info}”</div>}
              <ul className="mt-1 text-2xs text-muted-foreground">{(nd.reasons ?? []).map((r) => <li key={r}>• {r}</li>)}</ul>
              <div className="mt-2 flex min-w-0 items-center gap-2">
                <span className="label shrink-0">Correct match</span>
                <Select className="h-7 w-full min-w-0 flex-1" value={l.canonical_product_id ?? ""} onChange={(e) => relink(e.target.value)}>
                  <option value="">— not a tracked product —</option>
                  {(products ?? []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>
        <div className="min-w-0 space-y-3">
          {o.length ? o.map((x) => <OpportunityPanel key={x.id} o={x} onChange={() => mutate()} />) : (
            <Card><Empty><AlertTriangle className="mx-auto mb-1 size-4" />No valuation: listing not matched to a product with enough data, or not active.</Empty></Card>
          )}
          {l.price_history.length > 1 && (
            <Card>
              <CardHeader><CardTitle>Price history ({l.price_drop_count} reduction{l.price_drop_count === 1 ? "" : "s"})</CardTitle></CardHeader>
              <CardContent>
                <PriceHistoryChart points={l.price_history} />
                <div className="mt-2 flex flex-wrap gap-3 text-2xs">
                  {l.price_history.map((p, i) => (
                    <span key={i} className="num">{dateTime(p.observed_at)}: {eur(p.price_eur)} {p.change_pct != null && <span className={p.change_pct < 0 ? "text-pos" : "text-neg"}>({pct(p.change_pct)})</span>}</span>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          <Card>
            <CardHeader><CardTitle>Comparable listings ({data.comparables.length})</CardTitle><span className="text-2xs text-muted-foreground">weight = similarity × evidence quality</span></CardHeader>
            {data.comparables.length ? (
              <Table>
                <THead><TR><TH>Listing</TH><TH>Market</TH><TH className="text-right">Price</TH><TH>Kind</TH><TH>Cond.</TH><TH className="text-right">Days on mkt</TH><TH className="text-right">Weight</TH></TR></THead>
                <TBody>
                  {data.comparables.map((c) => (
                    <TR key={c.id}>
                      <TD className="max-w-[320px] truncate"><Link className="hover:underline" href={`/listings/${c.id}`}>{c.title}</Link></TD>
                      <TD className="whitespace-nowrap">{mpLabel(c.marketplace_code)} {flag(c.country)}</TD>
                      <TD className="num text-right">{eur(c.price_eur)}</TD>
                      <TD><span className={cn("text-2xs", c.kind === "sold" ? "text-pos" : c.kind === "ended" ? "text-primary" : "text-muted-foreground")}>{c.kind}</span></TD>
                      <TD className="text-2xs">{humanize(c.condition)}</TD>
                      <TD className="num text-right">{c.days_on_market?.toFixed(0) ?? "—"}</TD>
                      <TD className="num text-right">{c.weight.toFixed(2)}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            ) : (
              <Empty>No comparables.</Empty>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
