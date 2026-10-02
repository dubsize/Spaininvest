"use client";
import useSWR from "swr";
import { PageHeader } from "@/components/app-shell";
import { SignedBarChart } from "@/components/charts";
import { Empty, ErrorBox, Loading, Stat } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { fetcher } from "@/lib/api";
import { eur, humanize, mpLabel, pct } from "@/lib/format";

function Breakdown({ title, rows, label }: { title: string; rows: { key: string; profit: number; n: number; roi: number | null }[]; label: (k: string) => string }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      {rows.length ? (
        <>
          <CardContent><SignedBarChart data={rows.map((r) => ({ ...r, name: label(r.key) }))} xKey="name" yKey="profit" label="Realised profit" height={160} /></CardContent>
          <Table>
            <THead><TR><TH>{title.split(" ").pop()}</TH><TH className="text-right">Deals</TH><TH className="text-right">Profit</TH><TH className="text-right">ROI</TH></TR></THead>
            <TBody>{rows.map((r) => <TR key={r.key}><TD>{label(r.key)}</TD><TD className="num text-right">{r.n}</TD><TD className="num text-right">{eur(r.profit)}</TD><TD className="num text-right">{pct(r.roi)}</TD></TR>)}</TBody>
          </Table>
        </>
      ) : <Empty>No sold deals yet.</Empty>}
    </Card>
  );
}

export default function PortfolioPage() {
  const { data: p, error, isLoading } = useSWR<any>("/portfolio", fetcher);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !p) return <Loading />;
  const aging = p.inventory_aging;
  return (
    <div className="space-y-3">
      <PageHeader title="Portfolio & capital" subtitle="Capital deployed, realised returns and capital velocity" />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
        <Stat label="Capital deployed" value={eur(p.capital_deployed)} sub={`${p.inventory_count} items in inventory`} />
        <Stat label="Est. inventory value" value={eur(p.estimated_inventory_value)} />
        <Stat label="Unrealised exp. profit" value={eur(p.unrealized_expected_profit)} tone="pos" />
        <Stat label="Realised profit" value={eur(p.realized_profit)} tone={p.realized_profit >= 0 ? "pos" : "neg"} sub={`${p.deals_sold} deals sold`} />
        <Stat label="Average ROI / holding" value={pct(p.average_roi)} sub={p.average_holding_days != null ? `${p.average_holding_days} days avg hold` : undefined} />
        <Stat label="Annualised return on capital" value={p.annualized_return_on_capital != null ? pct(p.annualized_return_on_capital, 0) : "—"} sub="capital-weighted" />
      </div>
      <div className="grid gap-3 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><CardTitle>Monthly realised profit</CardTitle></CardHeader>
          <CardContent>{p.monthly_realized_profit.length ? <SignedBarChart data={p.monthly_realized_profit} xKey="month" yKey="profit" label="Realised profit" /> : <Empty>No sales yet.</Empty>}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Inventory ageing</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {([["0_30", "< 30 days"], ["30_60", "30–60 days"], ["60_90", "60–90 days"], ["90_plus", "> 90 days"]] as const).map(([k, l]) => (
              <div key={k} className="flex items-center justify-between text-xs">
                <span className={k === "90_plus" && aging[k] ? "text-neg" : k === "60_90" && aging[k] ? "text-warn" : ""}>{l}</span>
                <span className="num">{aging[k]} items · {eur(p.inventory_aging_value[k])}</span>
              </div>
            ))}
            <p className="pt-2 text-2xs text-muted-foreground">Old inventory ties up capital — consider repricing items older than 60 days.</p>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-3 xl:grid-cols-3">
        <Breakdown title="Profit by category" rows={p.profit_by_category} label={humanize} />
        <Breakdown title="Profit by marketplace" rows={p.profit_by_marketplace} label={mpLabel} />
        <Breakdown title="Profit by country" rows={p.profit_by_country} label={(k) => k} />
      </div>
    </div>
  );
}
