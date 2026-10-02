"use client";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { eur } from "@/lib/format";

// Dark-surface steps of the validated reference palette (slot 1 blue, slot 2 orange); red reserved for losses.
const SERIES_1 = "#3987e5";
const SERIES_2 = "#d95926";
const NEG = "#e66767";
const GRID = "hsl(220 13% 18%)";
const AXIS = { fontSize: 10, fill: "hsl(215 12% 62%)" };
const TOOLTIP = {
  contentStyle: { background: "hsl(220 16% 10%)", border: "1px solid hsl(220 13% 22%)", borderRadius: 6, fontSize: 11 },
  labelStyle: { color: "hsl(215 12% 70%)" },
  itemStyle: { color: "hsl(210 20% 92%)" },
};
const eurTick = (v: number) => (Math.abs(v) >= 10000 ? `€${Math.round(v / 1000)}k` : `€${Math.round(v)}`);
const shortDate = (v: string) => new Date(v).toLocaleDateString("es-ES", { day: "2-digit", month: "short" });

export function PriceHistoryChart({ points }: { points: { observed_at: string; price_eur: number }[] }) {
  const data = points.map((p) => ({ t: p.observed_at, price: p.price_eur }));
  return (
    <ResponsiveContainer width="100%" height={160}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="t" tickFormatter={shortDate} tick={AXIS} stroke={GRID} />
        <YAxis tickFormatter={eurTick} tick={AXIS} stroke={GRID} width={52} domain={["auto", "auto"]} />
        <Tooltip {...TOOLTIP} labelFormatter={(v) => new Date(v as string).toLocaleString("es-ES")} formatter={(v) => [eur(v as number), "Asking price"]} />
        <Line type="stepAfter" dataKey="price" stroke={SERIES_1} strokeWidth={2} dot={{ r: 4, fill: SERIES_1, stroke: "hsl(220 16% 10%)", strokeWidth: 2 }} activeDot={{ r: 5 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function HistogramChart({ bins, marker }: { bins: { from: number; to: number; count: number }[]; marker?: number | null }) {
  const data = bins.map((b) => ({ label: `${eurTick(b.from)}–${eurTick(b.to)}`, count: b.count, mid: (b.from + b.to) / 2, hit: marker != null && marker >= b.from && marker < b.to }));
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap={2}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="mid" tickFormatter={eurTick} tick={AXIS} stroke={GRID} />
        <YAxis allowDecimals={false} tick={AXIS} stroke={GRID} width={28} />
        <Tooltip {...TOOLTIP} cursor={{ fill: "hsl(220 14% 17% / 0.6)" }} labelFormatter={(_, p) => (p?.[0]?.payload?.label as string) ?? ""} formatter={(v) => [v as number, "Active listings"]} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={SERIES_1} fillOpacity={d.hit ? 1 : 0.6} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ValueTrendChart({ history }: { history: { t: string; market_value: number | null; quick_sale: number | null }[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={history} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="t" tickFormatter={shortDate} tick={AXIS} stroke={GRID} />
        <YAxis tickFormatter={eurTick} tick={AXIS} stroke={GRID} width={52} domain={["auto", "auto"]} />
        <Tooltip {...TOOLTIP} labelFormatter={(v) => new Date(v as string).toLocaleDateString("es-ES")} formatter={(v, n) => [eur(v as number), n]} />
        <Legend wrapperStyle={{ fontSize: 11 }} iconType="plainline" />
        <Line name="Market value" type="linear" dataKey="market_value" stroke={SERIES_1} strokeWidth={2} dot={{ r: 3 }} connectNulls />
        <Line name="Quick-sale" type="linear" dataKey="quick_sale" stroke={SERIES_2} strokeWidth={2} dot={{ r: 3 }} connectNulls />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SignedBarChart({ data, xKey, yKey, label, height = 200 }: { data: Record<string, any>[]; xKey: string; yKey: string; label: string; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap="20%">
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey={xKey} tick={AXIS} stroke={GRID} tickFormatter={(v: string) => (String(v).length > 11 ? `${String(v).slice(0, 10)}…` : v)} />
        <YAxis tickFormatter={eurTick} tick={AXIS} stroke={GRID} width={52} />
        <Tooltip {...TOOLTIP} cursor={{ fill: "hsl(220 14% 17% / 0.6)" }} formatter={(v) => [eur(v as number), label]} />
        <Bar dataKey={yKey} radius={[4, 4, 0, 0]} maxBarSize={56}>
          {data.map((d, i) => (
            <Cell key={i} fill={(d[yKey] as number) >= 0 ? SERIES_1 : NEG} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ScoreBars({ components }: { components: Record<string, any> }) {
  const keys = ["profit", "roi", "velocity", "discount", "liquidity", "confidence", "freshness"];
  return (
    <div className="space-y-1">
      {keys.map((k) => {
        const v = Number(components?.[k] ?? 0);
        return (
          <div key={k} className="flex items-center gap-2 text-2xs">
            <span className="w-20 capitalize text-muted-foreground">{k}</span>
            <div className="h-1.5 flex-1 rounded bg-muted">
              <div className="h-1.5 rounded bg-primary" style={{ width: `${Math.max(0, Math.min(100, v))}%` }} />
            </div>
            <span className="num w-8 text-right">{v.toFixed(0)}</span>
          </div>
        );
      })}
      {components?.risk_penalty ? (
        <div className="flex items-center gap-2 text-2xs">
          <span className="w-20 text-muted-foreground">risk penalty</span>
          <div className="h-1.5 flex-1 rounded bg-muted">
            <div className="h-1.5 rounded bg-neg" style={{ width: `${Math.min(100, Math.abs(components.risk_penalty))}%` }} />
          </div>
          <span className="num w-8 text-right text-neg">{Number(components.risk_penalty).toFixed(0)}</span>
        </div>
      ) : null}
    </div>
  );
}
