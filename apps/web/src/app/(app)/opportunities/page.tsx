"use client";
import { Suspense, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import useSWR from "swr";
import { Download, RotateCcw, SlidersHorizontal } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { OppTable, type SortState } from "@/components/opp-table";
import { Empty, ErrorBox, Loading } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { fetcher, qs } from "@/lib/api";
import { humanize, mpLabel } from "@/lib/format";
import type { Opportunity, Paged } from "@/lib/types";
import { cn } from "@/lib/utils";

const MULTI = ["type", "marketplace", "country", "brand", "category", "risk", "condition", "status"] as const;
const SINGLE = [
  "q", "city", "min_price", "max_price", "min_discount", "min_profit", "min_roi", "min_score", "max_age_hours",
  "min_seller_rating", "include_inactive", "price_dropped", "sort", "order", "page",
] as const;
const PCT_FIELDS = new Set(["min_discount", "min_roi"]);

function Chips({ options, value, onChange, render }: { options: string[]; value: string[]; onChange: (v: string[]) => void; render?: (v: string) => string }) {
  return (
    <div className="flex flex-wrap gap-1">
      {options.map((o) => {
        const on = value.includes(o);
        return (
          <button
            key={o}
            type="button"
            onClick={() => onChange(on ? value.filter((x) => x !== o) : [...value, o])}
            className={cn("rounded border px-1.5 py-0.5 text-2xs", on ? "border-primary bg-primary/20 text-foreground" : "text-muted-foreground hover:text-foreground")}
          >
            {render ? render(o) : o}
          </button>
        );
      })}
    </div>
  );
}

function Filters() {
  const router = useRouter();
  const path = usePathname();
  const sp = useSearchParams();
  const [showMore, setShowMore] = useState(true);

  const state = useMemo(() => {
    const s: Record<string, any> = {};
    for (const k of MULTI) s[k] = sp.getAll(k);
    for (const k of SINGLE) s[k] = sp.get(k) ?? "";
    return s;
  }, [sp]);

  const apiParams = useMemo(() => {
    const p: Record<string, any> = { ...state, page_size: 50, page: state.page || 1, sort: state.sort || "score", order: state.order || "desc" };
    for (const f of PCT_FIELDS) if (p[f] !== "") p[f] = Number(p[f]) / 100;
    return p;
  }, [state]);

  const { data: facets } = useSWR("/opportunities/facets", fetcher);
  const { data, error, isLoading } = useSWR<Paged<Opportunity>>(`/opportunities${qs(apiParams)}`, fetcher, { keepPreviousData: true, refreshInterval: 60000 });

  function update(patch: Record<string, any>, resetPage = true) {
    const next = { ...state, ...patch, ...(resetPage ? { page: "" } : {}) };
    router.replace(`${path}${qs(next)}`, { scroll: false });
  }

  const sort: SortState = { sort: state.sort || "score", order: (state.order as "asc" | "desc") || "desc" };
  const page = Number(state.page || 1);
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const exportHref = `/api/io/export/opportunities.csv${state.include_inactive ? "?include_inactive=true" : ""}`;

  const num = (k: string, placeholder: string, w = "w-24") => (
    <Input className={cn("h-7", w)} type="number" placeholder={placeholder} defaultValue={state[k]} key={`${k}-${state[k]}`} onBlur={(e) => e.target.value !== state[k] && update({ [k]: e.target.value })} onKeyDown={(e) => e.key === "Enter" && update({ [k]: (e.target as HTMLInputElement).value })} />
  );

  return (
    <div className="space-y-3">
      <PageHeader
        title="Opportunities"
        subtitle={data ? `${data.total} matching` : "…"}
        actions={
          <>
            <Button variant="outline" size="sm" onClick={() => setShowMore((v) => !v)}>
              <SlidersHorizontal /> Filters
            </Button>
            <Button variant="outline" size="sm" onClick={() => router.replace(path)}>
              <RotateCcw /> Reset
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href={exportHref}>
                <Download /> CSV
              </a>
            </Button>
          </>
        }
      />
      <Card className="space-y-2 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <Input className="h-7 w-64" placeholder="Search product or title…" defaultValue={state.q} key={`q-${state.q}`} onKeyDown={(e) => e.key === "Enter" && update({ q: (e.target as HTMLInputElement).value })} />
          <Chips options={["FLIP", "CROSS_BORDER", "NEGOTIATION"]} value={state.type} onChange={(v) => update({ type: v })} render={humanize} />
          <span className="mx-1 h-4 w-px bg-border" />
          <Chips options={["LOW", "MEDIUM", "HIGH"]} value={state.risk} onChange={(v) => update({ risk: v })} render={(r) => `risk ${r.toLowerCase()}`} />
          <span className="mx-1 h-4 w-px bg-border" />
          <label className="flex items-center gap-1 text-2xs text-muted-foreground">
            <input type="checkbox" checked={state.price_dropped === "true"} onChange={(e) => update({ price_dropped: e.target.checked ? "true" : "" })} /> price reduced
          </label>
          <label className="flex items-center gap-1 text-2xs text-muted-foreground">
            <input type="checkbox" checked={state.include_inactive === "true"} onChange={(e) => update({ include_inactive: e.target.checked ? "true" : "" })} /> include rejected/expired/non-deals
          </label>
        </div>
        {showMore && (
          <div className="grid gap-2 border-t pt-2 lg:grid-cols-2">
            <div className="space-y-1.5">
              <div className="flex items-start gap-2"><span className="label w-20 pt-0.5">Marketplace</span><Chips options={facets?.marketplaces ?? []} value={state.marketplace} onChange={(v) => update({ marketplace: v })} render={mpLabel} /></div>
              <div className="flex items-start gap-2"><span className="label w-20 pt-0.5">Country</span><Chips options={facets?.countries ?? []} value={state.country} onChange={(v) => update({ country: v })} /></div>
              <div className="flex items-start gap-2"><span className="label w-20 pt-0.5">Category</span><Chips options={facets?.categories ?? []} value={state.category} onChange={(v) => update({ category: v })} render={humanize} /></div>
              <div className="flex items-start gap-2"><span className="label w-20 pt-0.5">Condition</span><Chips options={facets?.conditions ?? []} value={state.condition} onChange={(v) => update({ condition: v })} render={humanize} /></div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-start gap-2"><span className="label w-20 pt-0.5">Brand</span><Chips options={facets?.brands ?? []} value={state.brand} onChange={(v) => update({ brand: v })} /></div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="label w-20">Price €</span>{num("min_price", "min")}{num("max_price", "max")}
                <span className="label">City</span>
                <Input className="h-7 w-28" placeholder="Madrid" defaultValue={state.city} key={`city-${state.city}`} onBlur={(e) => e.target.value !== state.city && update({ city: e.target.value })} />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="label w-20">Minimums</span>
                {num("min_profit", "profit €")}{num("min_roi", "ROI %")}{num("min_discount", "disc %")}{num("min_score", "score")}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="label w-20">Other</span>
                {num("max_age_hours", "max age h")}{num("min_seller_rating", "seller ≥", "w-20")}
                <Select className="h-7" value={state.status[0] ?? ""} onChange={(e) => update({ status: e.target.value ? [e.target.value] : [] })}>
                  <option value="">any status</option>
                  {["DISCOVERED", "WATCHING", "CONTACTED", "NEGOTIATING", "PURCHASED", "REJECTED", "SCAM_RISK", "EXPIRED"].map((s) => (
                    <option key={s} value={s}>{humanize(s.toLowerCase())}</option>
                  ))}
                </Select>
              </div>
            </div>
          </div>
        )}
      </Card>
      <Card>
        {error && <ErrorBox error={error} />}
        {isLoading && !data ? (
          <Loading />
        ) : data && data.items.length ? (
          <OppTable rows={data.items} sort={sort} onSort={(s) => update({ sort: s.sort, order: s.order })} />
        ) : (
          <Empty>No opportunities match these filters.</Empty>
        )}
        {data && pages > 1 && (
          <div className="flex items-center justify-end gap-2 border-t p-2 text-xs">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => update({ page: String(page - 1) }, false)}>Prev</Button>
            <span className="num text-muted-foreground">{page} / {pages}</span>
            <Button size="sm" variant="outline" disabled={page >= pages} onClick={() => update({ page: String(page + 1) }, false)}>Next</Button>
          </div>
        )}
      </Card>
    </div>
  );
}

export default function OpportunitiesPage() {
  return (
    <Suspense fallback={<Loading />}>
      <Filters />
    </Suspense>
  );
}
