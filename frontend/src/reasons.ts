/** Motifs de rejet du contrôle automatique (rejection_reasons), traduits pour le vendeur. */
const REASONS: Record<string, string> = {
  CONTACT_EMAIL: "le texte contient une adresse email",
  CONTACT_PHONE: "le texte contient un numéro de téléphone",
};

export function describeReason(code: string): string {
  return Object.hasOwn(REASONS, code) ? REASONS[code] : `motif inconnu (${code})`;
}
