import { ApiError } from "./errors";
import type { ProblemDetails } from "./types";

export interface RequestOptions {
  /** Adresse de base de l'API (catalogApiUrl ou notificationApiUrl), sans barre finale. */
  baseUrl: string;
  /** Chemin sous /api/v1, par exemple "/articles?limit=12". */
  path: string;
  method?: "GET" | "POST" | "PUT";
  body?: unknown;
  /** Jeton d'accès ; l'en-tête Authorization n'est ajouté que s'il est fourni. */
  token?: string | null;
  signal?: AbortSignal;
}

/**
 * Identifiant de corrélation conforme au contrat : au plus 128 caractères de [A-Za-z0-9._-].
 * Un UUID v4 (36 caractères, chiffres hexadécimaux et tirets) convient.
 */
export function newRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

/** Fonction unique d'appel des API : jeton, X-Request-ID et erreurs RFC 9457 traduites en ApiError. */
export async function apiRequest<T>(options: RequestOptions): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Request-ID": newRequestId(),
  };
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  if (options.body !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(`${options.baseUrl}${options.path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0);
  }

  if (!response.ok) {
    let problem: ProblemDetails | undefined;
    try {
      problem = (await response.json()) as ProblemDetails;
    } catch {
      problem = undefined;
    }
    throw new ApiError(response.status, problem);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
