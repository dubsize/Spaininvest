"use client";
import Link from "next/link";
import useSWR from "swr";
import { ArrowRight, Zap } from "lucide-react";
import { OppTable } from "@/components/opp-table";
import { PageHeader } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Empty, ErrorBox, Loading, Stat } from "@/components/states";
import { fetcher } from "@/lib/api";
import { ageFrom, eur, pct } from "@/lib/format";
import type { Opportunity } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Dashboard {
  kpis: Record<string, any>;
  deploy_now: Opportunity[];
  hottest: Opportunity[];
  newest: Opportunity[];
  highest_profit: Opportunity[];
  highest_roi: Opportunity[];
  highest_liquidity: Opportunity[];
  cross_border: Opportunity[];
  negotiation: Opportunity[];
  price_reduced: Opportunity[];
  connectors: { code: string; name: string; status: string; last_success_at: string | null }[];
  portfolio: Record<string, any>;
}

function Panel({ title, rows, href, hint }: { title: string; rows: Opportunity[]; href: string; hint?: string }) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle title={hint}>{title}</CardTitle>
        <Link href={href} className="inline-flex items-center gap-1 text-2xs text-muted-foreground hover:text-foreground">
          all <ArrowRight className="size-3" />
        </Link>
      </CardHeader>
      {rows.length ? <OppTable rows={rows} compact /> : <Empty>Nothing here right now.</Empty>}
    </Card>
  );
}

export default function DashboardPage() {
  const { data, error, isLoading } = useSWR<Dashboard>("/dashboard?limit=8", fetcher, { refreshInterval: 60000 });
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;
  const k = data.kpis;
  const p = data.portfolio;
  return (
    <div className="space-y-3">
      <PageHeader
        title="Where can I deploy €1 today for the best risk-adjusted return?"
        subtitle={
          <span>
            Ranked by net profit × capital velocity, adjusted for valuation confidence and risk · last scan{" "}
            {k.last_successful_scan ? `${ageFrom(k.last_successful_scan)} ago` : "never"}
          </span>
        }
      />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8">
        <Stat label="Actionable deals" value={k.actionable_deals} sub={`${k.active_opportunities} incl. negotiations`} />
        <Stat label="Expected net profit" value={eur(k.expected_profit_eur)} tone="pos" sub="low/medium-risk flips" />
        <Stat label="Capital required" value={eur(k.capital_required_eur)} />
        <Stat label="Avg ROI" value={pct(k.average_roi)} />
        <Stat label="New (24h)" value={k.new_last_24h} />
        <Stat label="Alerts (24h)" value={k.alerts_last_24h} />
        <Stat label="Realised profit" value={eur(p.realized_profit)} tone="pos" sub={`${p.deals_sold} deals sold`} />
        <Stat label="Capital deployed" value={eur(p.capital_deployed)} sub={`${p.inventory_count} items in stock`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5 text-foreground">
            <Zap className="size-3.5 text-warn" /> Deploy capital now — best risk-adjusted capital efficiency
          </CardTitle>
          <span className="text-2xs text-muted-foreground">annualised ROI × confidence × (1 − risk), excludes HIGH risk</span>
        </CardHeader>
        {data.deploy_now.length ? <OppTable rows={data.deploy_now} /> : <Empty>No actionable low/medium-risk deal right now.</Empty>}
      </Card>

      <div className="grid gap-3 xl:grid-cols-2">
        <Panel title="Hottest opportunities" rows={data.hottest} href="/opportunities?sort=score" />
        <Panel title="Newest" rows={data.newest} href="/opportunities?sort=published" />
        <Panel title="Highest expected profit" rows={data.highest_profit} href="/opportunities?sort=net_profit" />
        <Panel title="Highest ROI" rows={data.highest_roi} href="/opportunities?sort=roi" />
        <Panel title="Highest liquidity" rows={data.highest_liquidity} href="/opportunities?sort=liquidity" />
        <Panel title="Cross-border arbitrage" rows={data.cross_border} href="/opportunities?type=CROSS_BORDER" />
        <Panel title="Negotiation opportunities (old listings)" rows={data.negotiation} href="/opportunities?type=NEGOTIATION" />
        <Panel title="Recently price-reduced" rows={data.price_reduced} href="/opportunities?price_dropped=true&sort=price_drop" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connectors</CardTitle>
          <Link href="/scanner" className="text-2xs text-muted-foreground hover:text-foreground">
            scanner status →
          </Link>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {data.connectors.map((c) => (
            <div key={c.code} className="flex items-center gap-1.5 rounded border px-2 py-1 text-2xs">
              <span className={cn("size-1.5 rounded-full", c.status === "OK" ? "bg-pos" : c.status === "ERROR" ? "bg-neg" : "bg-warn")} />
              {c.name} <span className="text-muted-foreground">{c.status}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
