"use client";
import Link from "next/link";
import { ArrowDown, ArrowUp, TrendingDown } from "lucide-react";
import { LiquidityBadge, RiskBadge, ScoreBadge, TypeBadge } from "@/components/badges";
import { Thumb } from "@/components/thumb";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { ageFrom, eur, flag, mpLabel, pct } from "@/lib/format";
import type { Opportunity } from "@/lib/types";
import { cn } from "@/lib/utils";

export type SortState = { sort: string; order: "asc" | "desc" };

function SortTH({ label, k, sort, onSort, className }: { label: string; k?: string; sort?: SortState; onSort?: (s: SortState) => void; className?: string }) {
  if (!k || !onSort) return <TH className={className}>{label}</TH>;
  const active = sort?.sort === k;
  return (
    <TH className={className}>
      <button
        className={cn("inline-flex items-center gap-0.5 uppercase hover:text-foreground", active && "text-foreground")}
        onClick={() => onSort({ sort: k, order: active && sort?.order === "desc" ? "asc" : "desc" })}
      >
        {label}
        {active && (sort?.order === "desc" ? <ArrowDown className="size-3" /> : <ArrowUp className="size-3" />)}
      </button>
    </TH>
  );
}

export function profitOf(o: Opportunity): number | null {
  return o.opportunity_type === "NEGOTIATION" ? o.profit_at_target_offer_eur : o.net_profit_quick_eur;
}

export function OppTable({ rows, sort, onSort, compact = false }: { rows: Opportunity[]; sort?: SortState; onSort?: (s: SortState) => void; compact?: boolean }) {
  const now = Date.now();
  return (
    <Table>
      <THead>
        <TR className="hover:bg-transparent">
          <SortTH label="Score" k="score" sort={sort} onSort={onSort} className="w-12" />
          <TH>Product</TH>
          {!compact && <SortTH label="Market" k="marketplace" sort={sort} onSort={onSort} />}
          <SortTH label="Price" k="price" sort={sort} onSort={onSort} className="text-right" />
          {!compact && <SortTH label="Value" k="market_value" sort={sort} onSort={onSort} className="text-right" />}
          {!compact && <SortTH label="Quick sale" k="quick_sale" sort={sort} onSort={onSort} className="text-right" />}
          <SortTH label="Net profit" k="net_profit" sort={sort} onSort={onSort} className="text-right" />
          <SortTH label="ROI" k="roi" sort={sort} onSort={onSort} className="text-right" />
          {!compact && <SortTH label="Disc." k="discount" sort={sort} onSort={onSort} className="text-right" />}
          {!compact && <SortTH label="Ann. ROI" k="annualized_roi" sort={sort} onSort={onSort} className="text-right" />}
          {!compact && <SortTH label="Liq." k="liquidity" sort={sort} onSort={onSort} />}
          <SortTH label="Risk" k="risk" sort={sort} onSort={onSort} />
          <SortTH label="Age" k="published" sort={sort} onSort={onSort} className="text-right" />
        </TR>
      </THead>
      <TBody>
        {rows.map((o) => {
          const l = o.listing;
          const profit = profitOf(o);
          const name = o.canonical_product?.name ?? l.title;
          const variant = Object.entries(l.variant || {})
            .filter(([k]) => k !== "size" || name.includes("Cartier"))
            .map(([, v]) => v.replace(/_/g, " "))
            .join(" · ");
          return (
            <TR key={o.id} className="cursor-pointer">
              <TD>
                <Link href={`/listings/${o.listing_id}`}>
                  <ScoreBadge score={o.score} />
                </Link>
              </TD>
              <TD className={compact ? "max-w-[260px]" : "max-w-[340px]"}>
                <Link href={`/listings/${o.listing_id}`} className="flex items-center gap-2">
                  <Thumb src={l.image_urls?.[0]} title={name} size={compact ? 28 : 34} />
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <TypeBadge type={o.opportunity_type} />
                      <span className="truncate font-medium">{name}</span>
                    </div>
                    <div className="truncate text-2xs text-muted-foreground">
                      {variant && <span className="text-foreground/70">{variant} · </span>}
                      {compact ? `${flag(l.country)} ${mpLabel(l.marketplace_code)} · ` : ""}
                      {l.title}
                    </div>
                  </div>
                </Link>
              </TD>
              {!compact && (
                <TD className="whitespace-nowrap">
                  <div>{mpLabel(l.marketplace_code)}</div>
                  <div className="text-2xs text-muted-foreground">
                    {flag(l.country)} {l.city}
                  </div>
                </TD>
              )}
              <TD className="num whitespace-nowrap text-right">
                <div>{eur(o.purchase_price_eur)}</div>
                {o.opportunity_type === "NEGOTIATION" && o.target_offer_eur ? (
                  <div className="text-2xs text-warn">offer {eur(o.target_offer_eur)}</div>
                ) : l.price_drop_count > 0 && l.last_price_change_pct ? (
                  <div className="inline-flex items-center gap-0.5 text-2xs text-pos">
                    <TrendingDown className="size-3" /> {pct(l.last_price_change_pct, 0)}
                  </div>
                ) : null}
              </TD>
              {!compact && <TD className="num text-right text-muted-foreground">{eur(o.market_value_eur)}</TD>}
              {!compact && <TD className="num text-right">{eur(o.quick_sale_eur)}</TD>}
              <TD className={cn("num text-right font-semibold", (profit ?? 0) > 0 ? "text-pos" : "text-neg")}>{eur(profit)}</TD>
              <TD className="num text-right">{pct(o.opportunity_type === "NEGOTIATION" ? (o.score_components?.roi_at_target_offer ?? o.roi) : o.roi, 0)}</TD>
              {!compact && <TD className="num text-right">{pct(o.discount_pct, 0)}</TD>}
              {!compact && <TD className="num text-right text-muted-foreground">{o.annualized_roi != null ? pct(Math.min(o.annualized_roi, 99), 0) : "—"}</TD>}
              {!compact && (
                <TD>
                  <LiquidityBadge label={o.liquidity_label} score={o.liquidity_score} />
                </TD>
              )}
              <TD>
                <RiskBadge level={o.risk_level} />
              </TD>
              <TD className="num whitespace-nowrap text-right text-muted-foreground">{ageFrom(l.published_at ?? l.first_seen_at, now)}</TD>
            </TR>
          );
        })}
      </TBody>
    </Table>
  );
}
