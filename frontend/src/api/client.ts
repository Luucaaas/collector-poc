import { ApiError } from "./errors";
import type { ProblemDetails } from "./types";

export interface RequestOptions {
  /** Base address of the API (catalogApiUrl or notificationApiUrl), without trailing slash. */
  baseUrl: string;
  /** Path under /api/v1, for example "/articles?limit=12". */
  path: string;
  method?: "GET" | "POST" | "PUT";
  body?: unknown;
  /** Access token; the Authorization header is only added when it is provided. */
  token?: string | null;
  signal?: AbortSignal;
}

/**
 * Correlation identifier compliant with the contract: at most 128 characters of [A-Za-z0-9._-].
 * A UUID v4 (36 characters, hexadecimal digits and hyphens) fits.
 */
export function newRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

/** Single function for API calls: token, X-Request-ID and RFC 9457 errors translated into ApiError. */
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
