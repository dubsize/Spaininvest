"use client";
import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { ErrorBox, Loading } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Field, Input, Select } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { apiSend, fetcher } from "@/lib/api";
import { dateTime, eur, humanize, pct } from "@/lib/format";

const csv = (s: string) => s.split(/[,|]/).map((x) => x.trim()).filter(Boolean);

function WatchlistForm({ initial, onSaved }: { initial?: any; onSaved: () => void }) {
  const { data: products } = useSWR<any[]>("/products", fetcher);
  const { data: cats } = useSWR<any[]>("/settings/categories", fetcher);
  const [f, setF] = useState({
    name: initial?.name ?? "", keyword: initial?.keyword ?? "", canonical_product_id: initial?.canonical_product_id ?? "",
    category_code: initial?.category_code ?? "", brands: (initial?.brands ?? []).join(", "), countries: (initial?.countries ?? []).join(", "),
    marketplaces: (initial?.marketplaces ?? []).join(", "), max_price_eur: initial?.max_price_eur ?? "",
    min_discount: initial?.min_discount != null ? initial.min_discount * 100 : "", min_profit_eur: initial?.min_profit_eur ?? "",
    min_roi: initial?.min_roi != null ? initial.min_roi * 100 : "", min_score: initial?.min_score ?? "",
    priority: initial?.priority ?? "standard", scan_interval_minutes: initial?.scan_interval_minutes ?? "", enabled: initial?.enabled ?? true,
  });
  const [err, setErr] = useState<string | null>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<any>) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const n = (v: any) => (v === "" ? null : Number(v));
  async function save() {
    setErr(null);
    const body = {
      name: f.name, keyword: f.keyword, canonical_product_id: n(f.canonical_product_id), category_code: f.category_code || null,
      brands: csv(f.brands), countries: csv(f.countries).map((c) => c.toUpperCase()), marketplaces: csv(f.marketplaces),
      max_price_eur: n(f.max_price_eur), min_discount: f.min_discount === "" ? null : Number(f.min_discount) / 100,
      min_profit_eur: n(f.min_profit_eur), min_roi: f.min_roi === "" ? null : Number(f.min_roi) / 100, min_score: n(f.min_score),
      priority: f.priority, scan_interval_minutes: n(f.scan_interval_minutes), enabled: f.enabled,
    };
    try {
      if (initial?.id) await apiSend("PUT", `/watchlists/${initial.id}`, body);
      else await apiSend("POST", "/watchlists", body);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  return (
    <div className="grid grid-cols-2 gap-2">
      <Field label="Name" className="col-span-2"><Input value={f.name} onChange={set("name")} /></Field>
      <Field label="Search keyword"><Input value={f.keyword} onChange={set("keyword")} placeholder="Thermomix TM6" /></Field>
      <Field label="Canonical product">
        <Select className="w-full" value={f.canonical_product_id} onChange={set("canonical_product_id")}>
          <option value="">— any —</option>
          {(products ?? []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </Select>
      </Field>
      <Field label="Category">
        <Select className="w-full" value={f.category_code} onChange={set("category_code")}>
          <option value="">— any —</option>
          {(cats ?? []).map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
        </Select>
      </Field>
      <Field label="Brands (comma)"><Input value={f.brands} onChange={set("brands")} /></Field>
      <Field label="Countries (ES, FR…)"><Input value={f.countries} onChange={set("countries")} /></Field>
      <Field label="Marketplaces (codes)"><Input value={f.marketplaces} onChange={set("marketplaces")} placeholder="ebay_es, ebay_de" /></Field>
      <Field label="Max purchase price €"><Input type="number" value={f.max_price_eur} onChange={set("max_price_eur")} /></Field>
      <Field label="Min discount %"><Input type="number" value={f.min_discount} onChange={set("min_discount")} /></Field>
      <Field label="Min expected profit €"><Input type="number" value={f.min_profit_eur} onChange={set("min_profit_eur")} /></Field>
      <Field label="Min ROI %"><Input type="number" value={f.min_roi} onChange={set("min_roi")} /></Field>
      <Field label="Min Opportunity Score"><Input type="number" value={f.min_score} onChange={set("min_score")} /></Field>
      <Field label="Priority">
        <Select className="w-full" value={f.priority} onChange={set("priority")}>
          <option value="high">high (every few minutes)</option>
          <option value="standard">standard</option>
          <option value="background">background (slow)</option>
        </Select>
      </Field>
      <Field label="Custom interval (minutes)"><Input type="number" value={f.scan_interval_minutes} onChange={set("scan_interval_minutes")} placeholder="by priority" /></Field>
      <label className="flex items-center gap-2 pt-4 text-xs"><input type="checkbox" checked={f.enabled} onChange={set("enabled")} /> enabled</label>
      {err && <div className="col-span-2 text-xs text-neg">{err}</div>}
      <Button className="col-span-2" onClick={save}>{initial?.id ? "Save" : "Create watchlist"}</Button>
    </div>
  );
}

export default function WatchlistsPage() {
  const { data, error, isLoading, mutate } = useSWR<any[]>("/watchlists", fetcher);
  const [editing, setEditing] = useState<any | null>(null);
  const [creating, setCreating] = useState(false);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;
  return (
    <div className="space-y-3">
      <PageHeader
        title="Watchlists"
        subtitle="What the scanner searches for, how often, and which deals qualify"
        actions={
          <Dialog open={creating} onOpenChange={setCreating}>
            <DialogTrigger asChild><Button size="sm"><Plus /> New watchlist</Button></DialogTrigger>
            <DialogContent title="New watchlist" className="max-w-xl"><WatchlistForm onSaved={() => { setCreating(false); mutate(); }} /></DialogContent>
          </Dialog>
        }
      />
      <Card>
        <Table>
          <THead><TR><TH>Name</TH><TH>Keyword / product</TH><TH>Scope</TH><TH>Thresholds</TH><TH>Priority</TH><TH>Last / next scan</TH><TH /></TR></THead>
          <TBody>
            {data.map((w) => (
              <TR key={w.id} className={w.enabled ? "" : "opacity-50"}>
                <TD className="font-medium"><Link className="hover:underline" href={`/opportunities?${w.canonical_product_id ? `q=${encodeURIComponent(w.canonical_product?.name ?? "")}` : `q=${encodeURIComponent(w.keyword)}`}`}>{w.name}</Link></TD>
                <TD><div>{w.keyword || "—"}</div><div className="text-2xs text-muted-foreground">{w.canonical_product?.name ?? (w.category_code ? humanize(w.category_code) : "")}</div></TD>
                <TD className="text-2xs text-muted-foreground">{[w.countries.join("/"), w.marketplaces.join("/"), w.brands.join("/")].filter(Boolean).join(" · ") || "all"}</TD>
                <TD className="num text-2xs">
                  {[w.max_price_eur != null && `≤${eur(w.max_price_eur)}`, w.min_profit_eur != null && `profit ≥${eur(w.min_profit_eur)}`, w.min_roi != null && `ROI ≥${pct(w.min_roi, 0)}`, w.min_discount != null && `disc ≥${pct(w.min_discount, 0)}`, w.min_score != null && `score ≥${w.min_score}`].filter(Boolean).join(" · ") || "—"}
                </TD>
                <TD className="text-2xs">{w.priority}{w.scan_interval_minutes ? ` (${w.scan_interval_minutes}m)` : ""}</TD>
                <TD className="text-2xs text-muted-foreground">{dateTime(w.last_scanned_at)} / {dateTime(w.next_scan_at)}</TD>
                <TD className="whitespace-nowrap text-right">
                  <Button variant="ghost" size="icon" onClick={() => setEditing(w)} aria-label="Edit"><Pencil /></Button>
                  <Button variant="ghost" size="icon" aria-label="Delete" onClick={async () => { if (confirm(`Delete watchlist ${w.name}?`)) { await apiSend("DELETE", `/watchlists/${w.id}`); mutate(); } }}><Trash2 /></Button>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>
      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        {editing && <DialogContent title={`Edit ${editing.name}`} className="max-w-xl"><WatchlistForm initial={editing} onSaved={() => { setEditing(null); mutate(); }} /></DialogContent>}
      </Dialog>
    </div>
  );
}
