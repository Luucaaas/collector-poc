/** Rejection reasons of the automatic check (rejection_reasons), translated for the seller (French UI text). */
const REASONS: Record<string, string> = {
  CONTACT_EMAIL: "le texte contient une adresse email",
  CONTACT_PHONE: "le texte contient un numéro de téléphone",
};

/** What the seller should do about each reason. */
const ADVICE: Record<string, string> = {
  CONTACT_EMAIL: "Retirez l'adresse email du titre et de la description : les échanges passent par la plateforme.",
  CONTACT_PHONE: "Retirez le numéro de téléphone du titre et de la description : les échanges passent par la plateforme.",
};

export function describeReason(code: string): string {
  return Object.hasOwn(REASONS, code) ? REASONS[code] : `motif inconnu (${code})`;
}

export function adviceForReason(code: string): string | undefined {
  return Object.hasOwn(ADVICE, code) ? ADVICE[code] : undefined;
}

/** Short form for lists and badges. */
const SHORT_REASONS: Record<string, string> = {
  CONTACT_EMAIL: "adresse email dans le texte",
  CONTACT_PHONE: "numéro de téléphone dans le texte",
};

export function shortReason(code: string): string {
  return Object.hasOwn(SHORT_REASONS, code) ? SHORT_REASONS[code] : `motif inconnu (${code})`;
}
