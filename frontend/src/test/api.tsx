import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";
import { NotificationsProvider } from "../components/Notifications";
import { ToastProvider } from "../components/Toast";
import { ConfigContext } from "../config";

export const CONFIG = {
  authority: "https://auth.test/realms/collector",
  clientId: "collector-web",
  catalogApiUrl: "https://api.test/catalog/api/v1",
  notificationApiUrl: "https://api.test/notification/api/v1",
};

export interface Call {
  method: string;
  /** Path under /api/v1, with the query string. */
  path: string;
  body: unknown;
}

export const json = (data: unknown, status = 200) => Response.json(data, { status });
export const problem = (status: number, body: Record<string, unknown> = {}) =>
  new Response(JSON.stringify({ status, ...body }), { status, headers: { "Content-Type": "application/problem+json" } });

/** Mocks fetch: `handler` answers each call; returns the (live) list of calls received. */
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

/** Renders a page as a signed-in buyer: shared notifications feed (polling) and toasts, as in the Layout. */
export const renderAsBuyer = (ui: ReactElement) =>
  render(
    <ConfigContext.Provider value={CONFIG}>
      <ToastProvider>
        <NotificationsProvider enabled>
          <MemoryRouter>{ui}</MemoryRouter>
        </NotificationsProvider>
      </ToastProvider>
    </ConfigContext.Provider>,
  );

/** Renders a page with the toasts of the Layout. */
export const renderWithToasts = (ui: ReactElement) =>
  render(
    <ConfigContext.Provider value={CONFIG}>
      <ToastProvider>{ui}</ToastProvider>
    </ConfigContext.Provider>,
  );
