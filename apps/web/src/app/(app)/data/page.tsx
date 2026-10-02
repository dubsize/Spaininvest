"use client";
import { useState } from "react";
import { Download, Upload } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiSend } from "@/lib/api";

function Importer({ kind, title, help }: { kind: "listings" | "watchlists"; title: string; help: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle><a className="text-2xs text-primary hover:underline" href={`/api/io/templates/${kind}.csv`}>template</a></CardHeader>
      <CardContent className="space-y-2">
        <p className="text-xs text-muted-foreground">{help}</p>
        <input type="file" accept=".csv,text/csv" className="text-xs" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <Button
          size="sm"
          disabled={!file}
          onClick={async () => {
            setErr(null);
            setRes(null);
            const fd = new FormData();
            fd.append("file", file!);
            try {
              setRes(await apiSend("POST", `/io/import/${kind}`, fd));
            } catch (e) {
              setErr(e instanceof Error ? e.message : String(e));
            }
          }}
        >
          <Upload /> Import
        </Button>
        {err && <div className="text-xs text-neg">{err}</div>}
        {res && (
          <div className="text-xs">
            Created {res.created}{res.updated !== undefined ? `, updated ${res.updated}` : ""}.
            {res.errors?.length > 0 && <ul className="mt-1 text-neg">{res.errors.map((e: any) => <li key={e.row}>row {e.row}: {e.error}</li>)}</ul>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function DataPage() {
  return (
    <div className="max-w-4xl space-y-3">
      <PageHeader title="Import / export" subtitle="Human-readable CSV (UTF-8, opens in Excel / Google Sheets)" />
      <Card>
        <CardHeader><CardTitle>Export</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild><a href="/api/io/export/opportunities.csv"><Download /> Active deals</a></Button>
          <Button variant="outline" size="sm" asChild><a href="/api/io/export/opportunities.csv?include_inactive=true"><Download /> All evaluated listings</a></Button>
          <Button variant="outline" size="sm" asChild><a href="/api/io/export/price-history.csv"><Download /> Product price history</a></Button>
          <Button variant="outline" size="sm" asChild><a href="/api/io/export/watchlists.csv"><Download /> Watchlists</a></Button>
        </CardContent>
      </Card>
      <div className="grid gap-3 md:grid-cols-2">
        <Importer kind="listings" title="Import manually collected listings" help="Columns: url, title, price (required), currency, marketplace, country, city, description, condition, seller_*, published_at, shipping_cost, image_url, price_kind (asking|sold). Sold rows become high-weight comparables." />
        <Importer kind="watchlists" title="Import watchlists" help="Columns: name, keyword, product_slug, category, brands, countries, marketplaces (use | between values), max_price_eur, min_discount_pct, min_profit_eur, min_roi_pct, min_score, priority, scan_interval_minutes, enabled." />
      </div>
    </div>
  );
}
