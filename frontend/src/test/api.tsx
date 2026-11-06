import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { vi } from "vitest";
import { ConfigContext } from "../config";

export const CONFIG = {
  authority: "https://auth.test/realms/collector",
  clientId: "collector-web",
  catalogApiUrl: "https://api.test/catalog/api/v1",
  notificationApiUrl: "https://api.test/notification/api/v1",
};

export interface Call {
  method: string;
  /** Chemin sous /api/v1, avec la chaîne de requête. */
  path: string;
  body: unknown;
}

export const json = (data: unknown, status = 200) => Response.json(data, { status });
export const problem = (status: number, body: Record<string, unknown> = {}) =>
  new Response(JSON.stringify({ status, ...body }), { status, headers: { "Content-Type": "application/problem+json" } });

/** Simule fetch : `handler` répond à chaque appel ; renvoie la liste (vivante) des appels reçus. */
export function stubApi(handler: (call: Call) => Response): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string, init?: RequestInit) => {
      const url = new URL(input);
      const call: Call = {
        method: init?.method ?? "GET",
        path: url.pathname.replace(/^.*\/api\/v1/, "") + url.search,
        body: typeof init?.body === "string" ? JSON.parse(init.body) : undefined,
      };
      calls.push(call);
      return Promise.resolve(handler(call));
    }),
  );
  return calls;
}

export const renderWithConfig = (ui: ReactElement) =>
  render(<ConfigContext.Provider value={CONFIG}>{ui}</ConfigContext.Provider>);
