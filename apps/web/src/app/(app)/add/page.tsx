"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { Link2 } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { apiSend, fetcher } from "@/lib/api";
import { mpLabel } from "@/lib/format";

const CONDITIONS = ["", "new", "like_new", "very_good", "good", "fair", "for_parts"];

export default function AddListingPage() {
  const router = useRouter();
  const { data: products } = useSWR<any[]>("/products", fetcher);
  const [f, setF] = useState<Record<string, any>>({ url: "", title: "", price: "", currency: "EUR", marketplace: "", country: "", city: "", description: "", condition: "", seller_name: "", seller_rating: "", seller_rating_count: "", published_at: "", shipping_cost: "", shipping_available: "", image_url: "", canonical_product_id: "", price_kind: "asking" });
  const [info, setInfo] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: string) => (e: React.ChangeEvent<any>) => setF({ ...f, [k]: e.target.value });

  async function prefill(fetchMeta: boolean) {
    setErr(null);
    setInfo(null);
    setBusy(true);
    try {
      const r = await apiSend("POST", "/listings/manual/prefill", { url: f.url, fetch_metadata: fetchMeta });
      const md = r.metadata;
      setF((x) => ({
        ...x,
        marketplace: r.marketplace,
        country: r.country ?? x.country,
        title: x.title || md?.title || "",
        price: x.price || md?.price || "",
        currency: md?.currency || x.currency,
        description: x.description || md?.description || "",
        image_url: x.image_url || md?.image_urls?.[0] || "",
      }));
      setInfo(`Detected ${mpLabel(r.marketplace)}${r.country ? ` (${r.country})` : ""}. ${md?.error ? md.error : md?.fetched ? "Public page metadata loaded — please verify every field." : "Fill in the details manually."}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function submit() {
    setErr(null);
    setBusy(true);
    const n = (v: any) => (v === "" ? null : Number(v));
    try {
      const r = await apiSend("POST", "/listings/manual", {
        url: f.url, title: f.title, price: n(f.price), currency: f.currency, marketplace: f.marketplace || null, country: f.country || null,
        city: f.city || null, description: f.description, condition: f.condition || null, seller_name: f.seller_name || null,
        seller_rating: n(f.seller_rating), seller_rating_count: n(f.seller_rating_count), published_at: f.published_at ? new Date(f.published_at).toISOString() : null,
        shipping_cost: n(f.shipping_cost), shipping_available: f.shipping_available === "" ? null : f.shipping_available === "yes",
        image_urls: f.image_url ? [f.image_url] : [], canonical_product_id: n(f.canonical_product_id), price_kind: f.price_kind,
      });
      router.push(`/listings/${r.listing.id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-3">
      <PageHeader title="Add listing manually" subtitle="Works for any marketplace — including ones without a connector. The listing is normalised, valued against the price database and scored." />
      <Card>
        <CardHeader><CardTitle>1 · Listing URL</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          <div className="flex gap-2">
            <Input placeholder="https://es.wallapop.com/item/…" value={f.url} onChange={set("url")} />
            <Button variant="outline" disabled={!f.url || busy} onClick={() => prefill(false)}><Link2 /> Detect</Button>
            <Button variant="secondary" disabled={!f.url || busy} onClick={() => prefill(true)}>Fetch public details</Button>
          </div>
          <p className="text-2xs text-muted-foreground">“Fetch public details” makes one request to that page (only if its robots.txt allows it) and reads its OpenGraph / schema.org metadata. No crawling, no login.</p>
          {info && <p className="text-xs text-primary">{info}</p>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>2 · Details (fill or correct)</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-2 md:grid-cols-4">
          <Field label="Title" className="col-span-2 md:col-span-4"><Input value={f.title} onChange={set("title")} /></Field>
          <Field label="Price"><Input type="number" value={f.price} onChange={set("price")} /></Field>
          <Field label="Currency"><Select className="w-full" value={f.currency} onChange={set("currency")}>{["EUR", "GBP", "CHF", "USD", "SEK", "DKK", "PLN"].map((c) => <option key={c}>{c}</option>)}</Select></Field>
          <Field label="Price type"><Select className="w-full" value={f.price_kind} onChange={set("price_kind")}><option value="asking">asking (active)</option><option value="sold">sold (comparable)</option></Select></Field>
          <Field label="Marketplace code"><Input value={f.marketplace} onChange={set("marketplace")} placeholder="auto" /></Field>
          <Field label="Country"><Input value={f.country} onChange={set("country")} placeholder="ES" maxLength={2} /></Field>
          <Field label="City"><Input value={f.city} onChange={set("city")} /></Field>
          <Field label="Condition"><Select className="w-full" value={f.condition} onChange={set("condition")}>{CONDITIONS.map((c) => <option key={c} value={c}>{c || "detect from text"}</option>)}</Select></Field>
          <Field label="Published"><Input type="datetime-local" value={f.published_at} onChange={set("published_at")} /></Field>
          <Field label="Seller name"><Input value={f.seller_name} onChange={set("seller_name")} /></Field>
          <Field label="Seller rating (0-5)"><Input type="number" step="0.1" value={f.seller_rating} onChange={set("seller_rating")} /></Field>
          <Field label="# reviews"><Input type="number" value={f.seller_rating_count} onChange={set("seller_rating_count")} /></Field>
          <Field label="Shipping"><Select className="w-full" value={f.shipping_available} onChange={set("shipping_available")}><option value="">unknown</option><option value="yes">available</option><option value="no">pickup only</option></Select></Field>
          <Field label="Shipping cost"><Input type="number" value={f.shipping_cost} onChange={set("shipping_cost")} /></Field>
          <Field label="Image URL" className="col-span-2"><Input value={f.image_url} onChange={set("image_url")} /></Field>
          <Field label="Product (optional override)" className="col-span-2">
            <Select className="w-full" value={f.canonical_product_id} onChange={set("canonical_product_id")}>
              <option value="">auto-detect from title</option>
              {(products ?? []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </Select>
          </Field>
          <Field label="Description" className="col-span-2 md:col-span-4"><Textarea value={f.description} onChange={set("description")} className="min-h-28" /></Field>
        </CardContent>
      </Card>
      {err && <div className="text-xs text-neg">{err}</div>}
      <Button size="lg" disabled={busy || !f.title || !f.price} onClick={submit}>Analyse listing</Button>
    </div>
  );
}
