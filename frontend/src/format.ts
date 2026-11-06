const FORMATTERS = new Map<string, Intl.NumberFormat>();

/** Formate un montant en chaîne décimale ("120.00") en euros français : « 120,00 € ». */
export function formatMoney(amount: string, currency = "EUR"): string {
  let formatter = FORMATTERS.get(currency);
  if (!formatter) {
    formatter = new Intl.NumberFormat("fr-FR", { style: "currency", currency });
    FORMATTERS.set(currency, formatter);
  }
  // Intl.NumberFormat lit la chaîne décimale telle quelle, sans passer par un nombre flottant.
  return formatter.format(amount as `${number}`);
}
