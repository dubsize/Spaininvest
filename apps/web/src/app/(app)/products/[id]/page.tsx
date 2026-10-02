"use client";
import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { Pencil, RefreshCw, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { ConfidenceBadge } from "@/components/badges";
import { HistogramChart, ValueTrendChart } from "@/components/charts";
import { ProductForm } from "@/components/product-form";
import { Empty, ErrorBox, KV, Loading, Stat } from "@/components/states";
import { Thumb } from "@/components/thumb";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { apiSend, fetcher } from "@/lib/api";
import { ageFrom, eur, flag, humanize, mpLabel, pct } from "@/lib/format";
import type { ListingSummary } from "@/lib/types";
import { cn } from "@/lib/utils";

function ListingRows({ rows }: { rows: ListingSummary[] }) {
  if (!rows.length) return <Empty>No listings.</Empty>;
  return (
    <Table>
      <THead><TR><TH>Listing</TH><TH>Market</TH><TH>Variant</TH><TH className="text-right">Price</TH><TH>Status</TH><TH className="text-right">Age</TH></TR></THead>
      <TBody>
        {rows.map((l) => (
          <TR key={l.id}>
            <TD className="max-w-[360px]"><Link href={`/listings/${l.id}`} className="flex items-center gap-2 hover:underline"><Thumb src={l.image_urls[0]} title={l.title} size={24} /><span className="truncate">{l.title}</span></Link></TD>
            <TD className="whitespace-nowrap">{mpLabel(l.marketplace_code)} {flag(l.country)}</TD>
            <TD className="text-2xs text-muted-foreground">{Object.values(l.variant).join(" · ") || "—"}</TD>
            <TD className="num text-right">{eur(l.price_eur)}</TD>
            <TD className="text-2xs">{l.status}</TD>
            <TD className="num text-right text-muted-foreground">{ageFrom(l.published_at ?? l.first_seen_at)}</TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}

export default function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { data, error, isLoading, mutate } = useSWR<any>(`/products/${id}`, fetcher);
  const [variantIdx, setVariantIdx] = useState(0);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;
  const p = data.product;
  const variants: any[] = data.variants;
  const v = variants[Math.min(variantIdx, variants.length - 1)];
  const val = v?.valuation;

  return (
    <div className="space-y-3">
      <PageHeader
        title={p.name}
        subtitle={`${p.brand} · ${humanize(data.category.code)}${data.category.is_luxury ? " · luxury (authentication required)" : ""} · resale market ${flag(data.market)}`}
        actions={
          <>
            <Button variant="outline" size="sm" disabled={busy} onClick={async () => { setBusy(true); await apiSend("POST", `/products/${id}/renormalize`); setBusy(false); mutate(); }}>
              <RefreshCw /> Re-match listings
            </Button>
            <Dialog open={editing} onOpenChange={setEditing}>
              <DialogTrigger asChild><Button variant="outline" size="sm"><Pencil /> Edit</Button></DialogTrigger>
              <DialogContent title={`Edit ${p.name}`} className="max-w-2xl"><ProductForm initial={p} onSaved={() => { setEditing(false); mutate(); }} /></DialogContent>
            </Dialog>
            <Button variant="destructive" size="sm" onClick={async () => { if (confirm(`Delete ${p.name}? Listings are kept but unlinked.`)) { await apiSend("DELETE", `/products/${id}`); router.push("/products"); } }}>
              <Trash2 /> Delete
            </Button>
          </>
        }
      />
      {variants.length > 1 && (
        <div className="flex flex-wrap gap-1">
          {variants.map((x, i) => (
            <button key={x.variant_key} onClick={() => setVariantIdx(i)} className={cn("rounded border px-2 py-1 text-2xs", i === variantIdx ? "border-primary bg-primary/20" : "text-muted-foreground")}>
              {x.variant_key ? x.variant_key.replace(/;/g, " · ").replace(/_/g, " ") : "all variants"} <span className="num opacity-70">({x.valuation.n_comparables})</span>
            </button>
          ))}
        </div>
      )}
      {!v ? (
        <Card><Empty>No valuation yet — no comparable listings for this product.</Empty></Card>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-7">
            <Stat label="Market value" value={eur(val.market_value_eur)} sub={<ConfidenceBadge level={val.confidence_level} n={val.n_comparables} />} />
            <Stat label="Quick-sale" value={eur(val.quick_sale_eur)} />
            <Stat label="MAX BUY PRICE" value={eur(v.max_buy_price_eur)} tone="pos" sub={`target ROI ${pct(v.target_roi, 0)}`} />
            <Stat label="Opportunistic buy" value={eur(val.opportunistic_buy_eur)} />
            <Stat label="Comparables" value={val.n_comparables} sub={`${val.n_sold} sold · ${val.n_outliers} outliers removed`} />
            <Stat label="Dispersion (IQR)" value={pct(val.dispersion, 0)} sub={val.median_days_on_market != null ? `median ${val.median_days_on_market} days on market` : undefined} />
            <Stat label="30-day trend" value={v.trend_30d != null ? pct(v.trend_30d) : "—"} tone={v.trend_30d > 0 ? "pos" : v.trend_30d < 0 ? "neg" : undefined} />
          </div>
          <div className="grid gap-3 xl:grid-cols-3">
            <Card>
              <CardHeader><CardTitle>Value estimate</CardTitle></CardHeader>
              <CardContent>
                <KV k="Median asking (adj.)" v={eur(val.median_eur)} />
                <KV k="Trimmed mean" v={eur(val.trimmed_mean_eur)} />
                <KV k="25th percentile" v={eur(val.p25_eur)} />
                <KV k="75th percentile" v={eur(val.p75_eur)} />
                <KV k="Lowest reasonable" v={eur(val.lowest_reasonable_eur)} />
                <KV k="Quick-sale estimate" v={eur(val.quick_sale_eur)} />
                <KV k="Normal market price" v={eur(val.market_value_eur)} />
                <KV k="Confidence" v={`${val.confidence_level} (${(val.confidence_score * 100).toFixed(0)}%)`} />
                <ul className="mt-2 text-2xs text-muted-foreground">{val.notes.map((n: string) => <li key={n}>• {n}</li>)}</ul>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Price distribution (active listings)</CardTitle></CardHeader>
              <CardContent>
                {data.price_distribution.length ? <HistogramChart bins={data.price_distribution} marker={val.market_value_eur} /> : <Empty>No active listings.</Empty>}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Historical value ({v.variant_key || "all variants"})</CardTitle></CardHeader>
              <CardContent>{v.history.length > 1 ? <ValueTrendChart history={v.history} /> : <Empty>Not enough history yet.</Empty>}</CardContent>
            </Card>
          </div>
        </>
      )}
      <Card>
        <CardHeader><CardTitle>Marketplace comparison (active asks)</CardTitle></CardHeader>
        <Table>
          <THead><TR><TH>Marketplace</TH><TH>Country</TH><TH className="text-right">Listings</TH><TH className="text-right">Median</TH><TH className="text-right">Min</TH><TH className="text-right">Max</TH></TR></THead>
          <TBody>
            {data.marketplace_comparison.map((m: any) => (
              <TR key={m.marketplace + m.country}>
                <TD>{mpLabel(m.marketplace)}</TD><TD>{flag(m.country)} {m.country}</TD><TD className="num text-right">{m.n}</TD>
                <TD className="num text-right">{eur(m.median)}</TD><TD className="num text-right">{eur(m.min)}</TD><TD className="num text-right">{eur(m.max)}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>
      <div className="grid gap-3 xl:grid-cols-2">
        <Card><CardHeader><CardTitle>Active listings ({data.counts.active})</CardTitle></CardHeader><ListingRows rows={data.active_listings} /></Card>
        <Card><CardHeader><CardTitle>Recent listings (incl. ended)</CardTitle></CardHeader><ListingRows rows={data.recent_listings} /></Card>
      </div>
    </div>
  );
}
