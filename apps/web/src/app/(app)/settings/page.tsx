"use client";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Save, Send, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { ErrorBox, Loading } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Textarea } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiSend, fetcher } from "@/lib/api";
import { dateTime } from "@/lib/format";

function JsonGroup({ group, value, onSaved, help }: { group: string; value: any; onSaved: () => void; help: string }) {
  const [text, setText] = useState(JSON.stringify(value, null, 2));
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => setText(JSON.stringify(value, null, 2)), [value]);
  return (
    <Card>
      <CardHeader><CardTitle>{group}</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        <p className="text-xs text-muted-foreground">{help}</p>
        <Textarea className="min-h-[320px] font-mono" value={text} onChange={(e) => setText(e.target.value)} spellCheck={false} />
        <div className="flex items-center gap-2">
          <Button size="sm" onClick={async () => { try { await apiSend("PUT", `/settings/app/${group}`, JSON.parse(text)); setMsg("saved"); onSaved(); } catch (e) { setMsg(e instanceof Error ? e.message : String(e)); } }}><Save /> Save</Button>
          {msg && <span className="text-xs text-muted-foreground">{msg}</span>}
        </div>
      </CardContent>
    </Card>
  );
}

function EditableTable({ rows, columns, endpoint, onSaved, blank }: { rows: any[]; columns: { key: string; label: string; type?: "number" | "text" | "bool" | "pct"; w?: string }[]; endpoint: string; onSaved: () => void; blank?: any }) {
  const [draft, setDraft] = useState<Record<string, any>>({});
  const [err, setErr] = useState<string | null>(null);
  const val = (r: any, c: any) => {
    const d = draft[r.id ?? r.code]?.[c.key];
    if (d !== undefined) return d;
    const v = r[c.key];
    return c.type === "pct" && v != null ? +(v * 100).toFixed(3) : v ?? "";
  };
  const change = (r: any, k: string, v: any) => setDraft((d) => ({ ...d, [r.id ?? r.code]: { ...(d[r.id ?? r.code] ?? {}), [k]: v } }));
  async function save(r: any) {
    setErr(null);
    const body = { ...r };
    for (const c of columns) {
      const v = draft[r.id ?? r.code]?.[c.key];
      if (v === undefined) continue;
      body[c.key] = c.type === "number" ? (v === "" ? null : Number(v)) : c.type === "pct" ? (v === "" ? null : Number(v) / 100) : v === "" && c.type !== "text" ? null : v;
    }
    try {
      await apiSend(r.id === undefined && blank ? "POST" : "PUT", r.id === undefined ? (blank ? endpoint : `${endpoint}/${r.code}`) : `${endpoint}/${r.id}`, body);
      setDraft((d) => { const n = { ...d }; delete n[r.id ?? r.code]; return n; });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  return (
    <>
      {err && <div className="p-2 text-xs text-neg">{err}</div>}
      <Table>
        <THead><TR>{columns.map((c) => <TH key={c.key}>{c.label}</TH>)}<TH /></TR></THead>
        <TBody>
          {rows.map((r) => (
            <TR key={r.id ?? r.code}>
              {columns.map((c) => (
                <TD key={c.key} className="py-1">
                  {c.type === "bool" ? (
                    <input type="checkbox" checked={!!val(r, c)} onChange={(e) => change(r, c.key, e.target.checked)} />
                  ) : (
                    <Input className={`h-7 ${c.w ?? "w-24"}`} type={c.type === "number" || c.type === "pct" ? "number" : "text"} step="any" value={val(r, c)} onChange={(e) => change(r, c.key, e.target.value)} />
                  )}
                </TD>
              ))}
              <TD className="whitespace-nowrap">
                {draft[r.id ?? r.code] && <Button size="sm" onClick={() => save(r)}><Save /></Button>}
                {r.id !== undefined && blank && (
                  <Button size="icon" variant="ghost" aria-label="Delete" onClick={async () => { if (confirm("Delete this rule?")) { await apiSend("DELETE", `${endpoint}/${r.id}`); onSaved(); } }}><Trash2 /></Button>
                )}
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
      {blank && (
        <div className="border-t p-2">
          <Button size="sm" variant="outline" onClick={async () => { try { await apiSend("POST", endpoint, blank); onSaved(); } catch (e) { setErr(e instanceof Error ? e.message : String(e)); } }}>Add row</Button>
        </div>
      )}
    </>
  );
}

function AlertsTab() {
  const { data: rules, mutate } = useSWR<any[]>("/alerts/rules", fetcher);
  const { data: channels } = useSWR<any[]>("/alerts/channels", fetcher);
  const { data: events } = useSWR<any[]>("/alerts/events?limit=50", fetcher);
  const [msg, setMsg] = useState<string | null>(null);
  return (
    <div className="space-y-3">
      <Card>
        <CardHeader><CardTitle>Channels</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3 text-xs">
          {(channels ?? []).map((c) => (
            <span key={c.name} className="flex items-center gap-1.5">
              <span className={`size-1.5 rounded-full ${c.configured ? "bg-pos" : "bg-muted-foreground"}`} /> {c.name} {c.configured ? "" : "(not configured — see .env)"}
              {c.configured && <Button size="sm" variant="ghost" onClick={async () => { try { await apiSend("POST", `/alerts/channels/${c.name}/test`); setMsg(`${c.name}: test sent`); } catch (e) { setMsg(e instanceof Error ? e.message : String(e)); } }}><Send /> test</Button>}
            </span>
          ))}
          {msg && <span className="text-muted-foreground">{msg}</span>}
        </CardContent>
      </Card>
      {(rules ?? []).map((r) => <RuleEditor key={r.id} rule={r} onSaved={() => mutate()} />)}
      <Card>
        <CardHeader><CardTitle>Recent alerts (deduplicated per listing, channel & price)</CardTitle></CardHeader>
        <Table>
          <THead><TR><TH>When</TH><TH>Channel</TH><TH>Kind</TH><TH>Status</TH><TH>Message</TH></TR></THead>
          <TBody>
            {(events ?? []).map((e) => (
              <TR key={e.id}>
                <TD className="text-2xs">{dateTime(e.created_at)}</TD><TD className="text-2xs">{e.channel}</TD><TD className="text-2xs">{e.kind}</TD>
                <TD className={`text-2xs ${e.status === "failed" ? "text-neg" : ""}`}>{e.status}{e.error ? `: ${e.error}` : ""}</TD>
                <TD className="max-w-[480px] truncate text-2xs text-muted-foreground" title={e.message}>{e.message.split("\n").slice(0, 4).join(" · ")}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>
    </div>
  );
}

function RuleEditor({ rule, onSaved }: { rule: any; onSaved: () => void }) {
  const [text, setText] = useState(JSON.stringify(rule.conditions, null, 2));
  const [channels, setChannels] = useState((rule.channels ?? []).join(", "));
  const [maxRisk, setMaxRisk] = useState(rule.max_risk_level);
  const [enabled, setEnabled] = useState(rule.enabled);
  const [msg, setMsg] = useState<string | null>(null);
  return (
    <Card>
      <CardHeader><CardTitle>Rule: {rule.name}</CardTitle></CardHeader>
      <CardContent className="grid gap-2 md:grid-cols-[1fr_260px]">
        <Field label="Conditions (any group matches; all clauses in a group must match)" hint="fields: score, net_profit, roi, discount, price, price_to_quick_sale, liquidity, annualized_roi, confidence, risk_score">
          <Textarea className="min-h-[200px] font-mono" value={text} onChange={(e) => setText(e.target.value)} spellCheck={false} />
        </Field>
        <div className="space-y-2">
          <Field label="Channels"><Input value={channels} onChange={(e) => setChannels(e.target.value)} /></Field>
          <Field label="Max risk level"><Input value={maxRisk} onChange={(e) => setMaxRisk(e.target.value.toUpperCase())} /></Field>
          <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} /> enabled</label>
          <Button size="sm" onClick={async () => {
            try {
              await apiSend("PUT", `/alerts/rules/${rule.id}`, { ...rule, conditions: JSON.parse(text), channels: channels.split(",").map((s: string) => s.trim()).filter(Boolean), max_risk_level: maxRisk, enabled });
              setMsg("saved");
              onSaved();
            } catch (e) { setMsg(e instanceof Error ? e.message : String(e)); }
          }}><Save /> Save rule</Button>
          {msg && <div className="text-xs text-muted-foreground">{msg}</div>}
        </div>
      </CardContent>
    </Card>
  );
}

export default function SettingsPage() {
  const { data, error, isLoading, mutate } = useSWR<any>("/settings/app", fetcher);
  const { data: fees, mutate: mFees } = useSWR<any[]>("/settings/fees", fetcher);
  const { data: costs, mutate: mCosts } = useSWR<any[]>("/settings/costs", fetcher);
  const { data: cats, mutate: mCats } = useSWR<any[]>("/settings/categories", fetcher);
  const [busy, setBusy] = useState<string | null>(null);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;
  return (
    <div className="space-y-3">
      <PageHeader
        title="Settings"
        subtitle="All business rules are data — fees, costs, ROI targets, score weights and alert rules"
        actions={
          <>
            <Button size="sm" variant="outline" disabled={!!busy} onClick={async () => { setBusy("recompute"); const r = await apiSend("POST", "/settings/recompute"); setBusy(`re-scored ${r.listings_evaluated} listings`); }}>Recompute valuations &amp; scores</Button>
            <Button size="sm" variant="destructive" disabled={!!busy} onClick={async () => { if (confirm("Delete ALL demo listings, demo deals and their opportunities?")) { setBusy("purging"); const r = await apiSend("POST", "/settings/purge-demo"); setBusy(`deleted ${r.deleted_listings} demo listings`); } }}>Purge demo data</Button>
            {busy && <span className="text-xs text-muted-foreground">{busy}</span>}
          </>
        }
      />
      <Tabs defaultValue="business">
        <TabsList>
          <TabsTrigger value="business">Business</TabsTrigger>
          <TabsTrigger value="scoring">Scoring</TabsTrigger>
          <TabsTrigger value="fees">Fees</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="scanner">Scanner</TabsTrigger>
          <TabsTrigger value="valuation">Valuation</TabsTrigger>
        </TabsList>
        <TabsContent value="business"><JsonGroup group="business" value={data.business} onSaved={mutate} help="resale_countries: markets you resell in (default Spain). default_resale_marketplace / category_resale_marketplace decide which fee rules apply on resale. target_roi / min_roi are global defaults (categories and products can override). min_profit_eur feeds MAX BUY PRICE." /></TabsContent>
        <TabsContent value="scoring"><JsonGroup group="scoring" value={data.scoring} onSaved={mutate} help="weights of each score component (normalised), risk penalty, saturation scales, caps, freshness half-life, negotiation heuristics and liquidity thresholds. Changes apply on the next recompute." /></TabsContent>
        <TabsContent value="valuation"><JsonGroup group="valuation" value={data.valuation} onSaved={mutate} help="sold_weight, ended_weight, ask_to_sale discount, geography & staleness weights, outlier z-score, quick-sale quantile, minimum comparables." /></TabsContent>
        <TabsContent value="scanner"><JsonGroup group="scanner" value={data.scanner} onSaved={mutate} help="Watchlist cadence by priority (minutes), slow analysis cadence, expiry of listings not seen, max results per search, demo feed on/off. Per-marketplace polling floors are set on the Scanner page." /></TabsContent>
        <TabsContent value="fees">
          <Card>
            <CardHeader><CardTitle>Marketplace fee rules</CardTitle><span className="text-2xs text-warn">Seeded values are approximations — verify on each marketplace and tick “verified”.</span></CardHeader>
            <EditableTable rows={fees ?? []} endpoint="/settings/fees" onSaved={() => mFees()} blank={{ side: "sell", marketplace_code: "manual", percent: 0, fixed_eur: 0, notes: "new rule" }}
              columns={[{ key: "marketplace_code", label: "Marketplace", type: "text" }, { key: "side", label: "Side", type: "text", w: "w-14" }, { key: "category_code", label: "Category", type: "text" }, { key: "percent", label: "Fee %", type: "pct", w: "w-16" }, { key: "fixed_eur", label: "Fixed €", type: "number", w: "w-16" }, { key: "payment_percent", label: "Pay %", type: "pct", w: "w-16" }, { key: "payment_fixed_eur", label: "Pay €", type: "number", w: "w-16" }, { key: "min_fee_eur", label: "Min €", type: "number", w: "w-16" }, { key: "max_fee_eur", label: "Max €", type: "number", w: "w-16" }, { key: "active", label: "On", type: "bool" }, { key: "verified", label: "Verified", type: "bool" }, { key: "notes", label: "Notes", type: "text", w: "w-72" }]} />
          </Card>
        </TabsContent>
        <TabsContent value="costs">
          <Card>
            <CardHeader><CardTitle>Logistics cost profiles (route × shipping class / category)</CardTitle></CardHeader>
            <EditableTable rows={costs ?? []} endpoint="/settings/costs" onSaved={() => mCosts()} blank={{ name: "new profile", route: "domestic" }}
              columns={[{ key: "name", label: "Name", type: "text", w: "w-40" }, { key: "route", label: "Route", type: "text", w: "w-20" }, { key: "shipping_class", label: "Ship class", type: "text", w: "w-24" }, { key: "category_code", label: "Category", type: "text" }, { key: "inbound_shipping_eur", label: "Inbound €", type: "number", w: "w-16" }, { key: "outbound_shipping_eur", label: "Outbound €", type: "number", w: "w-16" }, { key: "insurance_pct", label: "Insur. %", type: "pct", w: "w-16" }, { key: "import_duty_pct", label: "Duty %", type: "pct", w: "w-16" }, { key: "import_vat_pct", label: "VAT %", type: "pct", w: "w-16" }, { key: "misc_eur", label: "Misc €", type: "number", w: "w-16" }, { key: "travel_eur", label: "Pickup €", type: "number", w: "w-16" }, { key: "active", label: "On", type: "bool" }]} />
          </Card>
        </TabsContent>
        <TabsContent value="categories">
          <Card>
            <CardHeader><CardTitle>Categories — per-category ROI targets, holding time, refurbishment & authentication</CardTitle></CardHeader>
            <EditableTable rows={cats ?? []} endpoint="/settings/categories" onSaved={() => mCats()}
              columns={[{ key: "name", label: "Name", type: "text", w: "w-36" }, { key: "is_luxury", label: "Luxury", type: "bool" }, { key: "authentication_required", label: "Auth req.", type: "bool" }, { key: "target_roi", label: "Target ROI %", type: "pct", w: "w-16" }, { key: "min_roi", label: "Min ROI %", type: "pct", w: "w-16" }, { key: "base_holding_days", label: "Hold days", type: "number", w: "w-16" }, { key: "refurbishment_eur", label: "Refurb €", type: "number", w: "w-16" }, { key: "authentication_eur", label: "Auth €", type: "number", w: "w-16" }, { key: "shipping_class", label: "Ship class", type: "text", w: "w-28" }]} />
          </Card>
        </TabsContent>
        <TabsContent value="alerts"><AlertsTab /></TabsContent>
      </Tabs>
    </div>
  );
}
