"use client";
import { useState } from "react";
import useSWR from "swr";
import { Play, Stethoscope } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { ErrorBox, Loading } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { apiSend, fetcher } from "@/lib/api";
import { ageFrom, dateTime, flag } from "@/lib/format";
import { cn } from "@/lib/utils";

const STATUS_TONE: Record<string, string> = { OK: "text-pos", DEGRADED: "text-warn", ERROR: "text-neg", STUB: "text-muted-foreground", NOT_CONFIGURED: "text-warn", DISABLED: "text-muted-foreground" };

export default function ScannerPage() {
  const { data, error, isLoading, mutate } = useSWR<any[]>("/scanner/marketplaces", fetcher, { refreshInterval: 30000 });
  const { data: runs, mutate: mutateRuns } = useSWR<any[]>("/scanner/runs?limit=60", fetcher, { refreshInterval: 30000 });
  const [msg, setMsg] = useState<Record<string, string>>({});
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading />;

  async function act(code: string, fn: () => Promise<string>) {
    setMsg((m) => ({ ...m, [code]: "…" }));
    try {
      const r = await fn();
      setMsg((m) => ({ ...m, [code]: r }));
    } catch (e) {
      setMsg((m) => ({ ...m, [code]: e instanceof Error ? e.message : String(e) }));
    }
    mutate();
    mutateRuns();
  }

  return (
    <div className="space-y-3">
      <PageHeader title="Scanner status" subtitle="Connector health, schedules and recent scan runs. Polling never runs faster than each marketplace's configured interval." />
      <Card>
        <Table>
          <THead>
            <TR><TH>Marketplace</TH><TH>Method</TH><TH>Status</TH><TH>Enabled</TH><TH>Interval</TH><TH>Last success</TH><TH>Next run</TH><TH className="text-right">24h scans / errors</TH><TH className="text-right">New 24h</TH><TH className="text-right">Collected</TH><TH /></TR>
          </THead>
          <TBody>
            {data.map((m) => (
              <TR key={m.code} className={cn(!m.enabled && "opacity-70")}>
                <TD><div className="font-medium">{flag(m.country)} {m.name}</div><div className="max-w-[340px] truncate text-2xs text-muted-foreground" title={m.compliance_notes}>{m.compliance_notes}</div></TD>
                <TD className="text-2xs">{m.compliance_method?.replace("_", " ")}</TD>
                <TD className={cn("text-2xs font-semibold", STATUS_TONE[m.status])}>{m.status.replace("_", " ")}{m.last_error && <div className="max-w-[200px] truncate font-normal text-neg" title={m.last_error}>{m.last_error}</div>}</TD>
                <TD>
                  <input
                    type="checkbox"
                    checked={m.enabled}
                    disabled={m.is_stub}
                    title={m.is_stub ? "No compliant automated connector — use manual entry / CSV" : undefined}
                    onChange={(e) => act(m.code, async () => { await apiSend("PATCH", `/scanner/marketplaces/${m.code}`, { enabled: e.target.checked }); return e.target.checked ? "enabled" : "disabled"; })}
                  />
                </TD>
                <TD className="num text-2xs">{Math.round(m.poll_interval_seconds / 60)} min · {m.max_requests_per_minute}/min</TD>
                <TD className="text-2xs">{m.last_success_at ? `${ageFrom(m.last_success_at)} ago` : "never"}</TD>
                <TD className="text-2xs">{m.enabled ? dateTime(m.next_run_at) : "—"}</TD>
                <TD className="num text-right text-2xs">{m.scans_24h} / <span className={m.errors_24h ? "text-neg" : ""}>{m.errors_24h}</span></TD>
                <TD className="num text-right text-2xs">{m.new_listings_24h}</TD>
                <TD className="num text-right text-2xs">{m.total_listings_collected}</TD>
                <TD className="whitespace-nowrap text-right">
                  {!m.is_stub && (
                    <>
                      <Button variant="ghost" size="icon" title="Health check" onClick={() => act(m.code, async () => { const h = await apiSend("POST", `/scanner/marketplaces/${m.code}/health`); return `${h.status}: ${h.message}`; })}><Stethoscope /></Button>
                      <Button variant="ghost" size="icon" title="Scan now" onClick={() => act(m.code, async () => { const r = await apiSend("POST", `/scanner/marketplaces/${m.code}/run`); return r.queued ? "queued" : `${r.run.status}: ${r.run.listings_new} new${r.run.error ? ` — ${r.run.error}` : ""}`; })}><Play /></Button>
                    </>
                  )}
                  {msg[m.code] && <div className="max-w-[220px] truncate text-2xs text-muted-foreground" title={msg[m.code]}>{msg[m.code]}</div>}
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>
      <Card>
        <CardHeader><CardTitle>Recent scan runs</CardTitle></CardHeader>
        <Table>
          <THead><TR><TH>Started</TH><TH>Marketplace</TH><TH>Query</TH><TH>Status</TH><TH className="text-right">Duration</TH><TH className="text-right">Found</TH><TH className="text-right">New</TH><TH className="text-right">Changed</TH><TH className="text-right">Price Δ</TH><TH className="text-right">Opps</TH><TH className="text-right">Alerts</TH><TH>Error</TH></TR></THead>
          <TBody>
            {(runs ?? []).map((r) => (
              <TR key={r.id}>
                <TD className="text-2xs">{dateTime(r.started_at)}</TD>
                <TD className="text-2xs">{r.marketplace_code}</TD>
                <TD className="max-w-[200px] truncate text-2xs text-muted-foreground">{r.query}</TD>
                <TD className={cn("text-2xs font-semibold", r.status === "success" ? "text-pos" : r.status === "error" ? "text-neg" : "text-muted-foreground")}>{r.status}</TD>
                <TD className="num text-right text-2xs">{r.duration_ms != null ? `${r.duration_ms} ms` : "—"}</TD>
                <TD className="num text-right text-2xs">{r.listings_found}</TD>
                <TD className="num text-right text-2xs">{r.listings_new}</TD>
                <TD className="num text-right text-2xs">{r.listings_updated}</TD>
                <TD className="num text-right text-2xs">{r.price_changes}</TD>
                <TD className="num text-right text-2xs">{r.opportunities_created}</TD>
                <TD className="num text-right text-2xs">{r.alerts_sent}</TD>
                <TD className="max-w-[260px] truncate text-2xs text-neg" title={r.error ?? ""}>{r.error}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>
    </div>
  );
}
