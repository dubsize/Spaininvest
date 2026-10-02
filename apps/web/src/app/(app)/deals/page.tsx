"use client";
import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import { BadgeEuro, Plus } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { StatusBadge } from "@/components/badges";
import { ErrorBox, Loading } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Field, Input, Select } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { apiSend, fetcher } from "@/lib/api";
import { date, eur, humanize, mpLabel, pct } from "@/lib/format";
import { cn } from "@/lib/utils";

const n = (v: string) => (v === "" ? 0 : Number(v));

function SellDialog({ deal, onDone }: { deal: any; onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ sale_price_eur: String(deal.expected_sale_price_eur ?? ""), sale_marketplace: "wallapop", sale_date: new Date().toISOString().slice(0, 10), sale_fees_eur: "", sale_shipping_eur: "", sale_other_costs_eur: "" });
  const [err, setErr] = useState<string | null>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button size="sm" variant="secondary"><BadgeEuro /> SOLD</Button></DialogTrigger>
      <DialogContent title={`Record sale — ${deal.title}`}>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Sale price €"><Input type="number" value={f.sale_price_eur} onChange={set("sale_price_eur")} /></Field>
          <Field label="Marketplace"><Input value={f.sale_marketplace} onChange={set("sale_marketplace")} /></Field>
          <Field label="Sale date"><Input type="date" value={f.sale_date} onChange={set("sale_date")} /></Field>
          <Field label="Actual fees €"><Input type="number" value={f.sale_fees_eur} onChange={set("sale_fees_eur")} /></Field>
          <Field label="Shipping €"><Input type="number" value={f.sale_shipping_eur} onChange={set("sale_shipping_eur")} /></Field>
          <Field label="Other costs €"><Input type="number" value={f.sale_other_costs_eur} onChange={set("sale_other_costs_eur")} /></Field>
        </div>
        {err && <div className="mt-2 text-xs text-neg">{err}</div>}
        <Button
          className="mt-3 w-full"
          onClick={async () => {
            try {
              await apiSend("POST", `/deals/${deal.id}/sell`, {
                sale_price_eur: n(f.sale_price_eur), sale_marketplace: f.sale_marketplace, sale_date: new Date(f.sale_date).toISOString(),
                sale_fees_eur: n(f.sale_fees_eur), sale_shipping_eur: n(f.sale_shipping_eur), sale_other_costs_eur: n(f.sale_other_costs_eur),
              });
              setOpen(false);
              onDone();
            } catch (e) {
              setErr(e instanceof Error ? e.message : String(e));
            }
          }}
        >
          Save sale
        </Button>
      </DialogContent>
    </Dialog>
  );
}

function NewDealDialog({ onDone }: { onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ title: "", category_code: "", source_marketplace: "", source_country: "ES", purchase_price_eur: "", purchase_date: new Date().toISOString().slice(0, 10), purchase_shipping_eur: "", repair_cost_eur: "", authentication_cost_eur: "", other_purchase_cost_eur: "", expected_sale_price_eur: "" });
  const [err, setErr] = useState<string | null>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button size="sm"><Plus /> Record purchase</Button></DialogTrigger>
      <DialogContent title="Record a purchase made outside the scanner">
        <div className="grid grid-cols-2 gap-2">
          <Field label="Item" className="col-span-2"><Input value={f.title} onChange={set("title")} /></Field>
          <Field label="Category code"><Input value={f.category_code} onChange={set("category_code")} placeholder="cameras" /></Field>
          <Field label="Bought on (marketplace)"><Input value={f.source_marketplace} onChange={set("source_marketplace")} /></Field>
          <Field label="Country"><Input value={f.source_country} onChange={set("source_country")} /></Field>
          <Field label="Price €"><Input type="number" value={f.purchase_price_eur} onChange={set("purchase_price_eur")} /></Field>
          <Field label="Date"><Input type="date" value={f.purchase_date} onChange={set("purchase_date")} /></Field>
          <Field label="Shipping €"><Input type="number" value={f.purchase_shipping_eur} onChange={set("purchase_shipping_eur")} /></Field>
          <Field label="Repair €"><Input type="number" value={f.repair_cost_eur} onChange={set("repair_cost_eur")} /></Field>
          <Field label="Authentication €"><Input type="number" value={f.authentication_cost_eur} onChange={set("authentication_cost_eur")} /></Field>
          <Field label="Other €"><Input type="number" value={f.other_purchase_cost_eur} onChange={set("other_purchase_cost_eur")} /></Field>
          <Field label="Expected sale €"><Input type="number" value={f.expected_sale_price_eur} onChange={set("expected_sale_price_eur")} /></Field>
        </div>
        {err && <div className="mt-2 text-xs text-neg">{err}</div>}
        <Button
          className="mt-3 w-full"
          onClick={async () => {
            try {
              await apiSend("POST", "/deals", {
                title: f.title, category_code: f.category_code || null, source_marketplace: f.source_marketplace || null, source_country: f.source_country || null,
                purchase_price_eur: n(f.purchase_price_eur), purchase_date: new Date(f.purchase_date).toISOString(), purchase_shipping_eur: n(f.purchase_shipping_eur),
                repair_cost_eur: n(f.repair_cost_eur), authentication_cost_eur: n(f.authentication_cost_eur), other_purchase_cost_eur: n(f.other_purchase_cost_eur),
                expected_sale_price_eur: f.expected_sale_price_eur ? n(f.expected_sale_price_eur) : null,
              });
              setOpen(false);
              onDone();
            } catch (e) {
              setErr(e instanceof Error ? e.message : String(e));
            }
          }}
        >
          Save
        </Button>
      </DialogContent>
    </Dialog>
  );
}

function Deals() {
  const sp = useSearchParams();
  const highlight = Number(sp.get("highlight"));
  const [status, setStatus] = useState("");
  const { data, error, isLoading, mutate } = useSWR<any[]>(`/deals${status ? `?status=${status}` : ""}`, fetcher);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;
  return (
    <div className="space-y-3">
      <PageHeader
        title="Deal tracker"
        subtitle="Actual results of what you buy — the data that will teach the system which categories make money"
        actions={
          <>
            <Select className="h-7" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">all statuses</option>
              {["PURCHASED", "RECEIVED", "LISTED_FOR_RESALE", "SOLD"].map((s) => <option key={s} value={s}>{humanize(s.toLowerCase())}</option>)}
            </Select>
            <NewDealDialog onDone={() => mutate()} />
          </>
        }
      />
      <Card>
        <Table>
          <THead>
            <TR><TH>Item</TH><TH>Status</TH><TH>Bought</TH><TH className="text-right">Total cost</TH><TH className="text-right">Expected sale</TH><TH className="text-right">Sale</TH><TH className="text-right">Profit</TH><TH className="text-right">ROI</TH><TH className="text-right">Days held</TH><TH className="text-right">Annualised</TH><TH /></TR>
          </THead>
          <TBody>
            {data.map((d) => {
              const m = d.metrics;
              return (
                <TR key={d.id} className={cn(d.id === highlight && "bg-primary/10")}>
                  <TD><div className="font-medium">{d.listing_id ? <Link className="hover:underline" href={`/listings/${d.listing_id}`}>{d.title}</Link> : d.title}</div><div className="text-2xs text-muted-foreground">{humanize(d.category_code)} · {mpLabel(d.source_marketplace)} {d.source_country}</div></TD>
                  <TD><StatusBadge status={d.status} /></TD>
                  <TD className="text-2xs">{date(d.purchase_date)}</TD>
                  <TD className="num text-right">{eur(m.total_cost)}</TD>
                  <TD className="num text-right text-muted-foreground">{eur(d.expected_sale_price_eur)}</TD>
                  <TD className="num text-right">{eur(d.sale_price_eur)}</TD>
                  <TD className={cn("num text-right font-semibold", m.profit == null ? "" : m.profit >= 0 ? "text-pos" : "text-neg")}>{m.profit == null ? <span className="font-normal text-muted-foreground">exp. {eur(d.expected_profit_eur)}</span> : eur(m.profit)}</TD>
                  <TD className="num text-right">{pct(m.roi)}</TD>
                  <TD className="num text-right">{m.holding_days != null ? m.holding_days.toFixed(0) : "—"}</TD>
                  <TD className="num text-right">{m.annualized_return != null ? pct(m.annualized_return, 0) : "—"}</TD>
                  <TD className="whitespace-nowrap text-right">
                    {d.status !== "SOLD" && (
                      <div className="flex justify-end gap-1">
                        {d.status === "PURCHASED" && <Button size="sm" variant="ghost" onClick={async () => { await apiSend("POST", `/deals/${d.id}/status`, { status: "RECEIVED" }); mutate(); }}>Received</Button>}
                        {d.status !== "LISTED_FOR_RESALE" && <Button size="sm" variant="ghost" onClick={async () => { await apiSend("POST", `/deals/${d.id}/status`, { status: "LISTED_FOR_RESALE" }); mutate(); }}>Listed</Button>}
                        <SellDialog deal={d} onDone={() => mutate()} />
                      </div>
                    )}
                  </TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      </Card>
    </div>
  );
}

export default function DealsPage() {
  return (
    <Suspense fallback={<Loading />}>
      <Deals />
    </Suspense>
  );
}
