import { Loader2 } from "lucide-react";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 p-6 text-xs text-muted-foreground">
      <Loader2 className="size-4 animate-spin" /> {label}
    </div>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return <div className="m-2 rounded border border-neg/40 bg-neg/10 p-3 text-xs text-neg">Error: {msg}</div>;
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="p-6 text-center text-xs text-muted-foreground">{children}</div>;
}

export function Stat({ label, value, sub, tone }: { label: string; value: React.ReactNode; sub?: React.ReactNode; tone?: "pos" | "neg" | "warn" }) {
  const color = tone === "pos" ? "text-pos" : tone === "neg" ? "text-neg" : tone === "warn" ? "text-warn" : "";
  return (
    <div className="rounded-lg border bg-card px-3 py-2">
      <div className="label">{label}</div>
      <div className={`num mt-0.5 text-lg font-semibold ${color}`}>{value}</div>
      {sub && <div className="text-2xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

export function KV({ k, v, mono = true }: { k: string; v: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border/50 py-1 last:border-0">
      <span className="text-xs text-muted-foreground">{k}</span>
      <span className={`text-right text-xs ${mono ? "num" : ""}`}>{v}</span>
    </div>
  );
}
