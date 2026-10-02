"use client";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function csrfToken(): string {
  if (typeof document === "undefined") return "";
  const m = document.cookie.match(/(?:^|; )arbscan_csrf=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : "";
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 401 && typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
    throw new ApiError(401, "not authenticated");
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const body = await res.json();
      msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, msg);
  }
  const ct = res.headers.get("content-type") || "";
  return (ct.includes("application/json") ? res.json() : res.text()) as Promise<T>;
}

export async function apiGet<T = any>(path: string): Promise<T> {
  return handle<T>(await fetch(`/api${path}`, { credentials: "same-origin", cache: "no-store" }));
}

export async function apiSend<T = any>(method: "POST" | "PUT" | "PATCH" | "DELETE", path: string, body?: unknown): Promise<T> {
  const isForm = body instanceof FormData;
  return handle<T>(
    await fetch(`/api${path}`, {
      method,
      credentials: "same-origin",
      headers: { "X-CSRF-Token": csrfToken(), ...(isForm || body === undefined ? {} : { "Content-Type": "application/json" }) },
      body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
    }),
  );
}

export const fetcher = (path: string) => apiGet(path);

export function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0)) continue;
    if (Array.isArray(v)) v.forEach((x) => sp.append(k, String(x)));
    else sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}
