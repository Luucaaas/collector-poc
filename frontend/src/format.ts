const FORMATTERS = new Map<string, Intl.NumberFormat>();

/** Formats an amount given as a decimal string ("120.00") in French euros: "120,00 €". */
export function formatMoney(amount: string, currency = "EUR"): string {
  let formatter = FORMATTERS.get(currency);
  if (!formatter) {
    formatter = new Intl.NumberFormat("fr-FR", { style: "currency", currency });
    FORMATTERS.set(currency, formatter);
  }
  // Intl.NumberFormat reads the decimal string as is, without going through a floating-point number.
  return formatter.format(amount as `${number}`);
}

/** Local date and time in French, from a UTC ISO 8601 date: "02/11/2026 15:05:00". */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "medium" });
}
