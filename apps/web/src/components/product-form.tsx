"use client";
import { useState } from "react";
import useSWR from "swr";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { apiSend, fetcher } from "@/lib/api";

const list = (s: string) => s.split(/\n|,/).map((x) => x.trim()).filter(Boolean);
const lines = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);

export function ProductForm({ initial, onSaved }: { initial?: any; onSaved: (p: any) => void }) {
  const { data: cats } = useSWR<{ code: string; name: string }[]>("/settings/categories", fetcher);
  const [f, setF] = useState({
    name: initial?.name ?? "",
    brand: initial?.brand ?? "",
    model: initial?.model ?? "",
    collection: initial?.collection ?? "",
    product_type: initial?.product_type ?? "",
    category_code: initial?.category_code ?? "kitchen_appliances",
    brand_aliases: (initial?.brand_aliases ?? []).join(", "),
    aliases: (initial?.aliases ?? []).join(", "),
    patterns: (initial?.patterns ?? []).join("\n"),
    reference_numbers: (initial?.reference_numbers ?? []).join(", "),
    required_keywords: (initial?.required_keywords ?? []).join(", "),
    excluded_keywords: (initial?.excluded_keywords ?? []).join("\n"),
    variant_attributes: JSON.stringify(initial?.variant_attributes ?? {}),
    attribute_rules: JSON.stringify(initial?.attribute_rules ?? {}, null, 0),
    retail_price_eur: initial?.retail_price_eur ?? "",
    popularity: initial?.popularity ?? 0.5,
    typical_holding_days: initial?.typical_holding_days ?? "",
    refurbishment_eur: initial?.refurbishment_eur ?? "",
    target_roi: initial?.target_roi != null ? initial.target_roi * 100 : "",
    is_active: initial?.is_active ?? true,
    notes: initial?.notes ?? "",
  });
  const [err, setErr] = useState<string | null>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<any>) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const opt = (v: any) => (v === "" || v === null ? null : Number(v));

  async function save() {
    setErr(null);
    let variant_attributes, attribute_rules;
    try {
      variant_attributes = JSON.parse(f.variant_attributes || "{}");
      attribute_rules = JSON.parse(f.attribute_rules || "{}");
    } catch {
      setErr("variant attributes / attribute rules must be valid JSON");
      return;
    }
    const body = {
      name: f.name, brand: f.brand, model: f.model, collection: f.collection || null, product_type: f.product_type || null,
      category_code: f.category_code, brand_aliases: list(f.brand_aliases), aliases: list(f.aliases), patterns: lines(f.patterns),
      reference_numbers: list(f.reference_numbers), required_keywords: list(f.required_keywords), excluded_keywords: lines(f.excluded_keywords),
      variant_attributes, attribute_rules, retail_price_eur: opt(f.retail_price_eur), popularity: Number(f.popularity),
      typical_holding_days: opt(f.typical_holding_days), refurbishment_eur: opt(f.refurbishment_eur),
      target_roi: f.target_roi === "" ? null : Number(f.target_roi) / 100, is_active: f.is_active, notes: f.notes,
    };
    try {
      const p = initial?.id ? await apiSend("PUT", `/products/${initial.id}`, body) : await apiSend("POST", "/products", body);
      onSaved(p);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <Field label="Display name"><Input value={f.name} onChange={set("name")} placeholder="Vorwerk Thermomix TM6" /></Field>
        <Field label="Category">
          <Select className="w-full" value={f.category_code} onChange={set("category_code")}>
            {(cats ?? []).map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
          </Select>
        </Field>
        <Field label="Brand"><Input value={f.brand} onChange={set("brand")} /></Field>
        <Field label="Model"><Input value={f.model} onChange={set("model")} /></Field>
        <Field label="Collection"><Input value={f.collection} onChange={set("collection")} /></Field>
        <Field label="Product type"><Input value={f.product_type} onChange={set("product_type")} placeholder="bracelet, bag, watch…" /></Field>
      </div>
      <Field label="Aliases (comma-separated, exact phrases)" hint="Strong matches, e.g. “love bracelet, pulsera love”. If empty and no patterns, the model name is used.">
        <Input value={f.aliases} onChange={set("aliases")} />
      </Field>
      <Field label="Regex patterns (one per line, matched on lower-case accent-free text)"><Textarea value={f.patterns} onChange={set("patterns")} className="font-mono" /></Field>
      <div className="grid grid-cols-2 gap-2">
        <Field label="Brand aliases"><Input value={f.brand_aliases} onChange={set("brand_aliases")} /></Field>
        <Field label="Reference numbers / SKUs"><Input value={f.reference_numbers} onChange={set("reference_numbers")} /></Field>
        <Field label="Required keywords (any of)"><Input value={f.required_keywords} onChange={set("required_keywords")} /></Field>
        <Field label="Excluded keywords (one per line, re: for regex)"><Textarea value={f.excluded_keywords} onChange={set("excluded_keywords")} className="min-h-[38px] font-mono" /></Field>
      </div>
      <Field label='Variant attributes JSON — importance 0..1 (≥0.8 = must match)' hint='e.g. {"material": 1.0, "size": 0.3}'>
        <Input value={f.variant_attributes} onChange={set("variant_attributes")} className="font-mono" />
      </Field>
      <Field label="Attribute rules JSON" hint='e.g. {"chip": [{"pattern": "\\bm([1-4])\\s*pro\\b", "value": "m{0}_pro"}]}'>
        <Textarea value={f.attribute_rules} onChange={set("attribute_rules")} className="font-mono" />
      </Field>
      <div className="grid grid-cols-4 gap-2">
        <Field label="Retail €"><Input type="number" value={f.retail_price_eur} onChange={set("retail_price_eur")} /></Field>
        <Field label="Popularity 0-1"><Input type="number" step="0.05" min="0" max="1" value={f.popularity} onChange={set("popularity")} /></Field>
        <Field label="Holding days"><Input type="number" value={f.typical_holding_days} onChange={set("typical_holding_days")} /></Field>
        <Field label="Target ROI %"><Input type="number" value={f.target_roi} onChange={set("target_roi")} placeholder="category" /></Field>
        <Field label="Refurb €"><Input type="number" value={f.refurbishment_eur} onChange={set("refurbishment_eur")} placeholder="category" /></Field>
        <label className="col-span-3 flex items-center gap-2 pt-4 text-xs"><input type="checkbox" checked={f.is_active} onChange={set("is_active")} /> active (used for matching & valuation)</label>
      </div>
      {err && <div className="text-xs text-neg">{err}</div>}
      <Button className="w-full" onClick={save}>{initial?.id ? "Save product" : "Create product"}</Button>
    </div>
  );
}
