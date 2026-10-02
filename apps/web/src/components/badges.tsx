import { AlertTriangle, ShieldAlert, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function ScoreBadge({ score, className }: { score: number; className?: string }) {
  const tone = score >= 80 ? "bg-pos/20 text-pos ring-pos/40" : score >= 60 ? "bg-primary/20 text-primary ring-primary/40" : score >= 40 ? "bg-warn/15 text-warn ring-warn/30" : "bg-muted text-muted-foreground ring-border";
  return (
    <span className={cn("num inline-flex h-6 min-w-9 items-center justify-center rounded px-1.5 text-xs font-bold ring-1", tone, className)} title="Opportunity Score (0-100)">
      {Math.round(score)}
    </span>
  );
}

export function RiskBadge({ level }: { level: string }) {
  if (level === "HIGH")
    return (
      <Badge variant="neg">
        <ShieldAlert className="size-3" aria-hidden /> HIGH
      </Badge>
    );
  if (level === "MEDIUM")
    return (
      <Badge variant="warn">
        <AlertTriangle className="size-3" aria-hidden /> MED
      </Badge>
    );
  return (
    <Badge variant="pos">
      <ShieldCheck className="size-3" aria-hidden /> LOW
    </Badge>
  );
}

export function ConfidenceBadge({ level, n }: { level?: string | null; n?: number }) {
  const v = level === "HIGH" ? "pos" : level === "MEDIUM" ? "default" : level === "LOW" ? "warn" : "neg";
  return (
    <Badge variant={v as any} title={n !== undefined ? `Based on ${n} comparables` : undefined}>
      {level ?? "—"}
      {n !== undefined && <span className="font-normal opacity-80">· {n}</span>}
    </Badge>
  );
}

export function LiquidityBadge({ label, score }: { label?: string | null; score?: number | null }) {
  const v = label === "High" ? "pos" : label === "Medium" ? "default" : "secondary";
  return (
    <Badge variant={v as any} title={score != null ? `Liquidity ${score.toFixed(0)}/100` : undefined}>
      {label ?? "—"}
    </Badge>
  );
}

const TYPE_STYLE: Record<string, { label: string; cls: string }> = {
  FLIP: { label: "FLIP", cls: "bg-primary/15 text-primary" },
  CROSS_BORDER: { label: "X-BORDER", cls: "bg-violet-500/15 text-violet-300" },
  NEGOTIATION: { label: "NEGOTIATE", cls: "bg-warn/15 text-warn" },
  NONE: { label: "—", cls: "bg-muted text-muted-foreground" },
};

export function TypeBadge({ type }: { type: string }) {
  const s = TYPE_STYLE[type] ?? TYPE_STYLE.NONE;
  return <span className={cn("whitespace-nowrap rounded px-1.5 py-0.5 text-2xs font-bold tracking-wide", s.cls)}>{s.label}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "SOLD" ? "pos" : status === "REJECTED" || status === "SCAM_RISK" ? "neg" : status === "EXPIRED" ? "secondary" : status === "DISCOVERED" ? "outline" : "default";
  return <Badge variant={tone as any}>{status.replace(/_/g, " ")}</Badge>;
}
