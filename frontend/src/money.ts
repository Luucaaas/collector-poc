const AMOUNT = /^\d{1,7}(?:[.,]\d{1,2})?$/;

/**
 * Normalise une saisie de montant en chaîne décimale à deux décimales ("12,5" → "12.50").
 * Renvoie null si le format n'est pas celui de l'API (7 chiffres au plus avant la virgule, 2 décimales
 * au plus). Aucune conversion en nombre : l'argent ne passe jamais par un flottant.
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

/** Contrôle de confort avant envoi (l'API refait la validation) : prix > 0 et au plus 1 000 000. */
export function validatePrice(input: string): { value: string } | { error: string } {
  const value = normalizeAmount(input);
  if (value === null) return { error: "Saisissez un montant valide, avec deux décimales au plus (ex. 120,00)." };
  const cents = toCents(value);
  if (cents <= 0) return { error: "Le prix doit être supérieur à 0." };
  if (cents > MAX_PRICE_CENTS) return { error: "Le prix ne peut pas dépasser 1 000 000 €." };
  return { value };
}

/** Frais de port : 0 autorisé (livraison gratuite). */
export function validateFee(input: string): { value: string } | { error: string } {
  const value = normalizeAmount(input);
  if (value === null) return { error: "Saisissez un montant valide, avec deux décimales au plus (ex. 8,00)." };
  if (toCents(value) > MAX_PRICE_CENTS) return { error: "Les frais de port ne peuvent pas dépasser 1 000 000 €." };
  return { value };
}
