"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";

const PALETTE = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9", "#e66767"];

export function Thumb({ src, title, size = 40, className }: { src?: string | null; title: string; size?: number; className?: string }) {
  const [failed, setFailed] = useState(false);
  const usable = src && !failed && !src.includes("demo.arbscan.local");
  const initials = title
    .split(/\s+/)
    .filter((w) => /^[A-Za-zÀ-ÿ]/.test(w))
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
  const color = PALETTE[Math.abs([...title].reduce((a, c) => a + c.charCodeAt(0), 0)) % PALETTE.length];
  return (
    <div className={cn("relative shrink-0 overflow-hidden rounded bg-muted", className)} style={{ width: size, height: size }}>
      {usable ? (
        <img src={src!} alt="" referrerPolicy="no-referrer" loading="lazy" className="h-full w-full object-cover" onError={() => setFailed(true)} />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-2xs font-bold text-white/90" style={{ background: `${color}55` }} aria-hidden>
          {initials || "?"}
        </div>
      )}
    </div>
  );
}
