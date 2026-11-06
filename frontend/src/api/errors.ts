import type { ProblemDetails } from "./types";

/** Erreur renvoyée par l'API (status > 0) ou erreur réseau (status 0). */
export class ApiError extends Error {
  readonly status: number;
  readonly codes: string[];
  readonly fields: { field?: string; code?: string }[];
  readonly correlationId?: string;

  constructor(status: number, problem?: ProblemDetails) {
    super(problem?.detail ?? problem?.title ?? `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.fields = problem?.errors ?? [];
    this.codes = this.fields.flatMap((e) => (e.code ? [e.code] : []));
    this.correlationId = problem?.correlation_id;
  }
}

/** Codes métier du contrat (contrats.md §2) et codes génériques de validation Pydantic. */
const CODE_MESSAGES: Record<string, string> = {
  CONTACT_EMAIL: "Le texte ne doit contenir aucune adresse email.",
  CONTACT_PHONE: "Le texte ne doit contenir aucun numéro de téléphone.",
  SHOP_NOT_FOUND: "La boutique choisie n'existe pas.",
  CATEGORY_NOT_FOUND: "La catégorie choisie n'existe pas.",
  TOO_MANY_CATEGORIES: "Vous ne pouvez pas choisir plus de 20 catégories.",
  NAME_ALREADY_USED: "Ce nom est déjà utilisé ou trop proche d'un nom existant.",
  NAME_INVALID: "Ce nom est invalide : il doit contenir au moins une lettre ou un chiffre.",
  MISSING: "champ obligatoire",
  STRING_TOO_SHORT: "texte trop court",
  STRING_TOO_LONG: "texte trop long",
  VALUE_ERROR: "valeur invalide",
  EXTRA_FORBIDDEN: "champ non autorisé",
  UUID_PARSING: "identifiant invalide",
};

/** Message d'un code connu ; `Object.hasOwn` écarte les clés héritées (`constructor`, `toString`...). */
function messageFor(code: string | undefined): string | undefined {
  return code !== undefined && Object.hasOwn(CODE_MESSAGES, code) ? CODE_MESSAGES[code] : undefined;
}

const BUSINESS_CODES = [
  "CONTACT_EMAIL",
  "CONTACT_PHONE",
  "SHOP_NOT_FOUND",
  "CATEGORY_NOT_FOUND",
  "TOO_MANY_CATEGORIES",
  "NAME_ALREADY_USED",
  "NAME_INVALID",
];

function validationMessage(error: ApiError): string {
  const business = [...new Set(error.codes.filter((c) => BUSINESS_CODES.includes(c)))];
  if (business.length > 0) return business.map((c) => CODE_MESSAGES[c]).join(" ");
  if (error.fields.length === 0) return "Les données saisies sont invalides.";
  const parts = error.fields.map((e) => {
    const reason = messageFor(e.code) ?? "valeur invalide";
    return e.field ? `${e.field} (${reason})` : reason;
  });
  return `Les données saisies sont invalides : ${parts.join(", ")}.`;
}

/** Message en français, destiné à l'utilisateur, pour n'importe quelle erreur levée par l'API. */
export function describeError(error: unknown): string {
  if (!(error instanceof ApiError)) return "Une erreur inattendue est survenue.";
  switch (error.status) {
    case 0:
      return "Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.";
    case 401:
      return "Vous n'êtes pas connecté ou votre session a expiré. Reconnectez-vous.";
    case 403:
      return "Vous n'avez pas le droit d'effectuer cette action.";
    case 404:
      return "La ressource demandée est introuvable.";
    case 409: {
      const message = error.codes.map(messageFor).find((m) => m !== undefined);
      return message ?? "Cette opération est en conflit avec l'état actuel des données.";
    }
    case 422:
      return validationMessage(error);
    default:
      return error.status >= 500
        ? "Le serveur a rencontré une erreur. Réessayez plus tard."
        : `La requête a échoué (HTTP ${error.status}).`;
  }
}
