const AMOUNT = /^\d{1,7}(?:[.,]\d{1,2})?$/;

/**
 * Normalizes an amount input to a decimal string with two decimals ("12,5" → "12.50").
 * Returns null if the format is not the API one (at most 7 digits before the comma, at most 2
 * decimals). No conversion to a number: money never goes through a float.
 */
export function normalizeAmount(input: string): string | null {
  const text = input.trim();
  if (!AMOUNT.test(text)) return null;
  const [integer, decimals = ""] = text.replace(",", ".").split(".");
  return `${integer}.${decimals.padEnd(2, "0")}`;
}

const MAX_PRICE_CENTS = 100_000_000; // 1 000 000,00 €

function toCents(amount: string): number {
  const [integer, decimals] = amount.split(".");
  return Number(integer) * 100 + Number(decimals);
}

/** Convenience check before sending (the API validates again): price > 0 and at most 1,000,000. */
export function validatePrice(input: string): { value: string } | { error: string } {
  const value = normalizeAmount(input);
  if (value === null) return { error: "Saisissez un montant valide, avec deux décimales au plus (ex. 120,00)." };
  const cents = toCents(value);
  if (cents <= 0) return { error: "Le prix doit être supérieur à 0." };
  if (cents > MAX_PRICE_CENTS) return { error: "Le prix ne peut pas dépasser 1 000 000 €." };
  return { value };
}

/** Shipping fee: 0 allowed (free delivery). */
export function validateFee(input: string): { value: string } | { error: string } {
  const value = normalizeAmount(input);
  if (value === null) return { error: "Saisissez un montant valide, avec deux décimales au plus (ex. 8,00)." };
  if (toCents(value) > MAX_PRICE_CENTS) return { error: "Les frais de port ne peuvent pas dépasser 1 000 000 €." };
  return { value };
}
