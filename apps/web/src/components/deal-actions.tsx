"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Calculator, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { KV } from "@/components/states";
import { apiSend } from "@/lib/api";
import { eur, pct } from "@/lib/format";
import type { Opportunity } from "@/lib/types";

const PRE_PURCHASE = ["DISCOVERED", "WATCHING", "CONTACTED", "NEGOTIATING", "REJECTED", "SCAM_RISK", "EXPIRED"];

export function StatusControl({ opp, onChange }: { opp: Opportunity; onChange: () => void }) {
  const [err, setErr] = useState<string | null>(null);
  if (!PRE_PURCHASE.includes(opp.status)) return null;
  return (
    <div className="flex items-center gap-1.5">
      <span className="label">Status</span>
      <Select
        className="h-7"
        value={opp.status}
        onChange={async (e) => {
          setErr(null);
          try {
            await apiSend("POST", `/opportunities/${opp.id}/status`, { status: e.target.value });
            onChange();
          } catch (ex) {
            setErr(ex instanceof Error ? ex.message : String(ex));
          }
        }}
      >
        {PRE_PURCHASE.map((s) => (
          <option key={s} value={s}>{s.replace("_", " ")}</option>
        ))}
      </Select>
      {err && <span className="text-2xs text-neg">{err}</span>}
    </div>
  );
}

const num = (v: string) => (v === "" ? 0 : Number(v));

export function PurchaseDialog({ opp, onDone }: { opp: Opportunity; onDone: () => void }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({
    purchase_price_eur: String(opp.target_offer_eur ?? opp.purchase_price_eur),
    purchase_date: new Date().toISOString().slice(0, 10),
    purchase_shipping_eur: "",
    repair_cost_eur: "",
    authentication_cost_eur: "",
    other_purchase_cost_eur: "",
    expected_sale_price_eur: String(opp.quick_sale_eur ?? ""),
    notes: "",
  });
  const [err, setErr] = useState<string | null>(null);
  if (!PRE_PURCHASE.slice(0, 4).includes(opp.status)) return null;
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });

  async function submit() {
    setErr(null);
    try {
      const r = await apiSend("POST", `/opportunities/${opp.id}/purchase`, {
        purchase_price_eur: num(f.purchase_price_eur),
        purchase_date: new Date(f.purchase_date).toISOString(),
        purchase_shipping_eur: num(f.purchase_shipping_eur),
        repair_cost_eur: num(f.repair_cost_eur),
        authentication_cost_eur: num(f.authentication_cost_eur),
        other_purchase_cost_eur: num(f.other_purchase_cost_eur),
        expected_sale_price_eur: f.expected_sale_price_eur ? num(f.expected_sale_price_eur) : null,
        notes: f.notes,
      });
      setOpen(false);
      onDone();
      router.push(`/deals?highlight=${r.deal_id}`);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><ShoppingCart /> PURCHASED</Button>
      </DialogTrigger>
      <DialogContent title="Record purchase" description="Moves this opportunity into the deal tracker.">
        <div className="grid grid-cols-2 gap-2">
          <Field label="Negotiated price €"><Input type="number" value={f.purchase_price_eur} onChange={set("purchase_price_eur")} /></Field>
          <Field label="Purchase date"><Input type="date" value={f.purchase_date} onChange={set("purchase_date")} /></Field>
          <Field label="Actual shipping €"><Input type="number" value={f.purchase_shipping_eur} onChange={set("purchase_shipping_eur")} /></Field>
          <Field label="Repair cost €"><Input type="number" value={f.repair_cost_eur} onChange={set("repair_cost_eur")} /></Field>
          <Field label="Authentication €"><Input type="number" value={f.authentication_cost_eur} onChange={set("authentication_cost_eur")} /></Field>
          <Field label="Other cost €"><Input type="number" value={f.other_purchase_cost_eur} onChange={set("other_purchase_cost_eur")} /></Field>
          <Field label="Expected sale €" className="col-span-2"><Input type="number" value={f.expected_sale_price_eur} onChange={set("expected_sale_price_eur")} /></Field>
          <Field label="Notes" className="col-span-2"><Textarea value={f.notes} onChange={set("notes")} /></Field>
        </div>
        {err && <div className="mt-2 text-xs text-neg">{err}</div>}
        <Button className="mt-3 w-full" onClick={submit}>Save purchase</Button>
      </DialogContent>
    </Dialog>
  );
}

export function OfferCalculator({ opp }: { opp: Opportunity }) {
  const [f, setF] = useState({
    target_roi: String(Math.round((opp.score_components?.target_roi ?? 0.25) * 100)),
    target_profit_eur: "",
    expected_resale: String(opp.quick_sale_eur ?? ""),
    expected_costs_eur: "",
  });
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });

  async function calc() {
    setErr(null);
    try {
      setRes(
        await apiSend("POST", `/opportunities/${opp.id}/offer`, {
          target_roi: num(f.target_roi) / 100,
          target_profit_eur: num(f.target_profit_eur),
          expected_resale: f.expected_resale ? num(f.expected_resale) : null,
          expected_costs_eur: f.expected_costs_eur ? num(f.expected_costs_eur) : null,
        }),
      );
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    }
  }

  return (
    <Dialog onOpenChange={(o) => o && !res && calc()}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline"><Calculator /> WHAT SHOULD I OFFER?</Button>
      </DialogTrigger>
      <DialogContent title="What should I offer?" description="Leave expected costs empty to use the configured fee & cost rules.">
        <div className="grid grid-cols-2 gap-2">
          <Field label="Target net ROI %"><Input type="number" value={f.target_roi} onChange={set("target_roi")} /></Field>
          <Field label="Target absolute profit €"><Input type="number" value={f.target_profit_eur} onChange={set("target_profit_eur")} /></Field>
          <Field label="Expected resale €"><Input type="number" value={f.expected_resale} onChange={set("expected_resale")} /></Field>
          <Field label="Expected costs € (optional)"><Input type="number" value={f.expected_costs_eur} onChange={set("expected_costs_eur")} placeholder="fee engine" /></Field>
        </div>
        <Button className="mt-2 w-full" variant="secondary" onClick={calc}>Calculate</Button>
        {err && <div className="mt-2 text-xs text-neg">{err}</div>}
        {res && (
          <div className="mt-3 rounded border p-3">
            <KV k="Seller asking" v={eur(res.asking_price)} />
            <KV k="Ideal offer" v={<span className="text-base font-bold text-pos">{eur(res.ideal_offer)}</span>} />
            <KV k="Maximum buy price" v={<span className="font-semibold">{eur(res.max_acceptable_offer)}</span>} />
            <KV k="Expected resale" v={eur(res.expected_resale)} />
            <KV k="Expected costs" v={eur(res.expected_costs)} />
            <KV k="Profit at ideal offer" v={`${eur(res.expected_profit_at_ideal)} (${pct(res.expected_roi_at_ideal)})`} />
            <KV k="Profit at max price" v={eur(res.expected_profit_at_max)} />
            <KV k="Profit at asking price" v={`${eur(res.expected_profit_at_ask)} (${pct(res.roi_at_ask)})`} />
            <p className="mt-2 text-xs text-muted-foreground">{res.note}</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
