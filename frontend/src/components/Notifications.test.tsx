import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { json, problem, stubApi, CONFIG } from "../test/api";
import { ConfigContext } from "../config";
import { NOTIFICATIONS_POLL_MS, NotificationsProvider, useNotifications } from "./Notifications";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: { access_token: "buyer-token" } }) }));

function Probe() {
  const feed = useNotifications();
  return (
    <div>
      <p data-testid="total">{feed.total === null ? "unknown" : feed.total}</p>
      <p data-testid="loading">{String(feed.loading)}</p>
      <p data-testid="message">{feed.message ?? ""}</p>
      <button onClick={feed.refresh}>refresh</button>
    </div>
  );
}

function setVisibility(state: "visible" | "hidden") {
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => state });
  document.dispatchEvent(new Event("visibilitychange"));
}

const mount = (enabled = true) =>
  render(
    <ConfigContext.Provider value={CONFIG}>
      <NotificationsProvider enabled={enabled}>
        <Probe />
      </NotificationsProvider>
    </ConfigContext.Provider>,
  );
const count = (calls: { path: string }[]) => calls.filter((c) => c.path.startsWith("/me/notifications")).length;
const advance = (ms: number) => act(() => vi.advanceTimersByTimeAsync(ms));

beforeEach(() => {
  vi.useFakeTimers();
  setVisibility("visible");
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  // @ts-expect-error restore the real property of jsdom
  delete document.visibilityState;
});

describe("NotificationsProvider: periodic polling", () => {
  it("loads at mount, then every 10 seconds, and updates the total", async () => {
    let total = 2;
    const calls = stubApi(() => json({ items: [], total }));
    mount();
    await advance(0);
    expect(count(calls)).toBe(1);
    expect(screen.getByTestId("total")).toHaveTextContent("2");

    total = 3;
    await advance(NOTIFICATIONS_POLL_MS - 1);
    expect(count(calls)).toBe(1);
    await advance(1);
    expect(count(calls)).toBe(2);
    expect(screen.getByTestId("total")).toHaveTextContent("3");
    await advance(NOTIFICATIONS_POLL_MS);
    expect(count(calls)).toBe(3);
  });

  it("never stacks two requests: the next one waits for the end of the previous one", async () => {
    let resolve: (r: Response) => void = () => {};
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        calls.push(url);
        return new Promise<Response>((r) => (resolve = r));
      }),
    );
    mount();
    await advance(0);
    await advance(60_000);
    expect(calls).toHaveLength(1);
    expect(screen.getByTestId("loading")).toHaveTextContent("true");

    resolve(json({ items: [], total: 1 }));
    await advance(0);
    expect(screen.getByTestId("total")).toHaveTextContent("1");
    await advance(NOTIFICATIONS_POLL_MS);
    expect(calls).toHaveLength(2);
  });

  it("ignores a manual refresh while a request is running, and refreshes at once otherwise", async () => {
    const calls = stubApi(() => json({ items: [], total: 0 }));
    mount();
    await advance(0);
    expect(count(calls)).toBe(1);
    await act(async () => screen.getByRole("button", { name: "refresh" }).click());
    await advance(0);
    expect(count(calls)).toBe(2);
    // the timer was restarted by the manual refresh: no extra call 10 s after the first one
    await advance(NOTIFICATIONS_POLL_MS - 1);
    expect(count(calls)).toBe(2);
    await advance(1);
    expect(count(calls)).toBe(3);
  });

  it("stops while the tab is hidden, cancels the running request, and resumes at once when visible again", async () => {
    const signals: AbortSignal[] = [];
    let calls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        calls += 1;
        if (init?.signal) signals.push(init.signal);
        return Promise.resolve(json({ items: [], total: calls }));
      }),
    );
    mount();
    await advance(0);
    expect(calls).toBe(1);

    setVisibility("hidden");
    await advance(120_000);
    expect(calls).toBe(1);

    setVisibility("visible");
    await advance(0);
    expect(calls).toBe(2);
    expect(screen.getByTestId("total")).toHaveTextContent("2");
    await advance(NOTIFICATIONS_POLL_MS);
    expect(calls).toBe(3);
    expect(signals).toHaveLength(3);
  });

  it("aborts the request in flight when the tab becomes hidden", async () => {
    const signals: AbortSignal[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        if (init?.signal) signals.push(init.signal);
        return new Promise<Response>(() => {});
      }),
    );
    mount();
    await advance(0);
    expect(signals[0]?.aborted).toBe(false);
    setVisibility("hidden");
    await advance(0);
    expect(signals[0]?.aborted).toBe(true);
    expect(screen.getByTestId("loading")).toHaveTextContent("false");
    setVisibility("visible");
    await advance(0);
    expect(signals).toHaveLength(2);
  });

  it("sends nothing while hidden at mount, and starts when the tab becomes visible", async () => {
    setVisibility("hidden");
    const calls = stubApi(() => json({ items: [], total: 4 }));
    mount();
    await advance(60_000);
    expect(count(calls)).toBe(0);
    setVisibility("visible");
    await advance(0);
    expect(count(calls)).toBe(1);
  });

  it("stops completely on unmount (no timer, no listener, request cancelled)", async () => {
    const calls = stubApi(() => json({ items: [], total: 1 }));
    const { unmount } = mount();
    await advance(0);
    expect(count(calls)).toBe(1);
    unmount();
    expect(vi.getTimerCount()).toBe(0);
    await advance(120_000);
    setVisibility("hidden");
    setVisibility("visible");
    await advance(0);
    expect(count(calls)).toBe(1);
  });

  it("sends nothing when not enabled (visitor, seller, admin)", async () => {
    const calls = stubApi(() => json({ items: [], total: 1 }));
    mount(false);
    await advance(60_000);
    expect(calls).toHaveLength(0);
    expect(screen.getByTestId("total")).toHaveTextContent("unknown");
  });

  it("keeps the last data after a failure, shows the message, and keeps polling", async () => {
    let fail = false;
    const calls = stubApi(() => (fail ? problem(500) : json({ items: [], total: 5 })));
    mount();
    await advance(0);
    expect(screen.getByTestId("total")).toHaveTextContent("5");
    fail = true;
    await advance(NOTIFICATIONS_POLL_MS);
    expect(screen.getByTestId("total")).toHaveTextContent("5");
    expect(screen.getByTestId("message")).not.toBeEmptyDOMElement();
    fail = false;
    await advance(NOTIFICATIONS_POLL_MS);
    expect(count(calls)).toBe(3);
    expect(screen.getByTestId("message")).toBeEmptyDOMElement();
  });
});
