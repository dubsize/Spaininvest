"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import useSWR from "swr";
import {
  Activity, BarChart3, Boxes, Briefcase, Database, Gauge, ListFilter, LogOut, PlusCircle, Radar, Settings, Telescope,
} from "lucide-react";
import { apiSend, fetcher } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/opportunities", label: "Opportunities", icon: ListFilter },
  { href: "/products", label: "Products", icon: Boxes },
  { href: "/watchlists", label: "Watchlists", icon: Telescope },
  { href: "/add", label: "Add listing", icon: PlusCircle },
  { href: "/deals", label: "Deal tracker", icon: Briefcase },
  { href: "/portfolio", label: "Portfolio", icon: BarChart3 },
  { href: "/scanner", label: "Scanner", icon: Radar },
  { href: "/data", label: "Import / export", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { data: me } = useSWR("/auth/me", fetcher);
  const { data: health } = useSWR("/health", fetcher, { refreshInterval: 60000 });

  async function logout() {
    try {
      await apiSend("POST", "/auth/logout");
    } finally {
      router.push("/login");
    }
  }

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-48 shrink-0 flex-col border-r bg-panel md:flex">
        <div className="flex items-center gap-2 border-b px-3 py-3">
          <Activity className="size-4 text-primary" />
          <div>
            <div className="text-sm font-bold tracking-tight">ArbScan</div>
            <div className="text-2xs text-muted-foreground">second-hand arbitrage</div>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 p-2">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? path === "/" : path.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2 rounded px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
                  active && "bg-accent text-foreground",
                )}
              >
                <Icon className="size-3.5" /> {label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t p-2 text-2xs text-muted-foreground">
          <div className="flex items-center gap-1.5 px-2 py-1">
            <span className={cn("size-1.5 rounded-full", health?.database ? "bg-pos" : "bg-neg")} />
            API {health?.status ?? "…"}
          </div>
          <button onClick={logout} className="flex w-full items-center gap-2 rounded px-2 py-1.5 hover:bg-accent hover:text-foreground">
            <LogOut className="size-3.5" /> {me?.username ?? "logout"}
          </button>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <nav className="flex gap-1 overflow-x-auto border-b bg-panel p-2 md:hidden">
          {NAV.map(({ href, label }) => (
            <Link key={href} href={href} className={cn("whitespace-nowrap rounded px-2 py-1 text-xs", path === href ? "bg-accent" : "text-muted-foreground")}>
              {label}
            </Link>
          ))}
        </nav>
        <main className="min-w-0 flex-1 p-3 md:p-4">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
      <div>
        <h1 className="text-base font-semibold tracking-tight">{title}</h1>
        {subtitle && <div className="text-xs text-muted-foreground">{subtitle}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
