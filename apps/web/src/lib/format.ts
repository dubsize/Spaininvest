const eur0 = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
const eur2 = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function eur(v: number | null | undefined, decimals = false): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return (decimals ? eur2 : eur0).format(v);
}

export function pct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(digits)}%`;
}

export function signedEur(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${v > 0 ? "+" : ""}${eur(v)}`;
}

export function ageFrom(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return "—";
  const mins = Math.max(0, Math.floor((now - new Date(iso).getTime()) / 60000));
  if (mins < 60) return `${mins} min`;
  if (mins < 48 * 60) return `${Math.floor(mins / 60)} h`;
  return `${Math.floor(mins / 1440)} d`;
}

export function dateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-ES", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function date(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
}

export function humanize(s: string | null | undefined): string {
  if (!s) return "—";
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export const COUNTRY_FLAG: Record<string, string> = { ES: "🇪🇸", FR: "🇫🇷", DE: "🇩🇪", IT: "🇮🇹", PT: "🇵🇹", GB: "🇬🇧", NL: "🇳🇱", BE: "🇧🇪" };
export const flag = (c?: string | null) => (c ? COUNTRY_FLAG[c] ?? c : "");

export const MARKETPLACE_LABEL: Record<string, string> = {
  wallapop: "Wallapop", leboncoin: "Leboncoin", ebay_es: "eBay ES", ebay_fr: "eBay FR", ebay_de: "eBay DE", ebay_it: "eBay IT",
  vinted_es: "Vinted ES", vinted_fr: "Vinted FR", vinted_de: "Vinted DE", vinted_it: "Vinted IT", kleinanzeigen: "Kleinanzeigen",
  milanuncios: "Milanuncios", vestiaire: "Vestiaire", chrono24: "Chrono24", catawiki: "Catawiki", facebook: "FB Marketplace",
  amazon_es: "Amazon ES", amazon_fr: "Amazon FR", amazon_de: "Amazon DE", amazon_it: "Amazon IT", manual: "Manual", demo_feed: "Demo feed",
};
export const mpLabel = (c?: string | null) => (c ? MARKETPLACE_LABEL[c] ?? c : "—");
