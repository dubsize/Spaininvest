"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { Plus, Wand2 } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { ConfidenceBadge } from "@/components/badges";
import { ProductForm } from "@/components/product-form";
import { ErrorBox, KV, Loading } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { apiSend, fetcher } from "@/lib/api";
import { eur, humanize, pct } from "@/lib/format";

function NormalizeTester() {
  const [title, setTitle] = useState("Pulsera Cartier Love T17 oro amarillo");
  const [res, setRes] = useState<any>(null);
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm"><Wand2 /> Test matcher</Button>
      </DialogTrigger>
      <DialogContent title="Normalisation tester" description="Paste any listing title in any language.">
        <div className="flex gap-2">
          <Input value={title} onChange={(e) => setTitle(e.target.value)} onKeyDown={async (e) => e.key === "Enter" && setRes(await apiSend("POST", "/products/normalize/test", { title }))} />
          <Button onClick={async () => setRes(await apiSend("POST", "/products/normalize/test", { title }))}>Test</Button>
        </div>
        {res && (
          <div className="mt-3">
            <KV k="Product" v={res.product_name ?? "— no match"} mono={false} />
            <KV k="Brand / model" v={`${res.brand ?? "—"} / ${res.model ?? "—"}`} mono={false} />
            <KV k="Attributes" v={JSON.stringify(res.attributes)} />
            <KV k="Condition" v={res.condition} />
            <KV k="Confidence" v={pct(res.confidence, 0)} />
            <ul className="mt-1 text-2xs text-muted-foreground">{res.reasons.map((r: string) => <li key={r}>• {r}</li>)}</ul>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function ProductsPage() {
  const { data, error, isLoading, mutate } = useSWR<any[]>("/products", fetcher);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const rows = useMemo(() => (data ?? []).filter((p) => !q || `${p.name} ${p.brand} ${p.category_code}`.toLowerCase().includes(q.toLowerCase())), [data, q]);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;
  return (
    <div className="space-y-3">
      <PageHeader
        title="Products (canonical catalogue)"
        subtitle={`${data.length} products · used by the normaliser to map listing titles in any language`}
        actions={
          <>
            <Input className="h-7 w-48" placeholder="Filter…" value={q} onChange={(e) => setQ(e.target.value)} />
            <NormalizeTester />
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild><Button size="sm"><Plus /> New product</Button></DialogTrigger>
              <DialogContent title="New product" className="max-w-2xl">
                <ProductForm onSaved={() => { setOpen(false); mutate(); }} />
              </DialogContent>
            </Dialog>
          </>
        }
      />
      <Card>
        <Table>
          <THead>
            <TR><TH>Product</TH><TH>Category</TH><TH className="text-right">Market value</TH><TH className="text-right">Quick sale</TH><TH>Confidence</TH><TH className="text-right">Active</TH><TH className="text-right">Opps</TH><TH /></TR>
          </THead>
          <TBody>
            {rows.map((p) => (
              <TR key={p.id} className={p.is_active ? "" : "opacity-50"}>
                <TD><Link href={`/products/${p.id}`} className="font-medium hover:underline">{p.name}</Link><div className="text-2xs text-muted-foreground">{p.brand} · {p.slug}</div></TD>
                <TD className="text-muted-foreground">{humanize(p.category_code)}</TD>
                <TD className="num text-right">{eur(p.market_value_eur)}</TD>
                <TD className="num text-right">{eur(p.quick_sale_eur)}</TD>
                <TD><ConfidenceBadge level={p.confidence_level} n={p.n_comparables} /></TD>
                <TD className="num text-right">{p.active_listings}</TD>
                <TD className="num text-right">{p.active_opportunities}</TD>
                <TD className="text-right"><Link href={`/products/${p.id}`} className="text-2xs text-primary hover:underline">open</Link></TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>
    </div>
  );
}
