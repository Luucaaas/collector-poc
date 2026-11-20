/** Rejection reasons of the automatic check (rejection_reasons), translated for the seller (French UI text). */
const REASONS: Record<string, string> = {
  CONTACT_EMAIL: "le texte contient une adresse email",
  CONTACT_PHONE: "le texte contient un numéro de téléphone",
};

export function describeReason(code: string): string {
  return Object.hasOwn(REASONS, code) ? REASONS[code] : `motif inconnu (${code})`;
}
