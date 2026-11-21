import { Box } from "@mui/material";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { AppNotification, Page } from "../api/types";
import { describeError } from "../api/errors";
import { useApi } from "../api/useApi";

export const NOTIFICATIONS_PAGE_SIZE = 10;
/** Delay between the end of a request and the start of the next one (never less: the API is shared). */
export const NOTIFICATIONS_POLL_MS = 10_000;

export interface NotificationsFeed {
  /** First page of notifications (the most recent ones), or null before the first answer. */
  page: Page<AppNotification> | null;
  /** French message of the last failed request, cleared by the next success. */
  message: string | null;
  /** True while a request is running. */
  loading: boolean;
  /** Time of the last successful answer. */
  updatedAt: Date | null;
  /** Total number of notifications of the buyer, or null when not known (not a buyer, or not loaded yet). */
  total: number | null;
  /** Asks for an immediate update; ignored while a request is running. */
  refresh: () => void;
}

const EMPTY: NotificationsFeed = {
  page: null,
  message: null,
  loading: false,
  updatedAt: null,
  total: null,
  refresh: () => {},
};

const FeedContext = createContext<NotificationsFeed>(EMPTY);

/** The single source of the buyer's notifications: the page and the navigation badge both read it. */
export const useNotifications = () => useContext(FeedContext);

interface FeedState {
  page: Page<AppNotification> | null;
  message: string | null;
  loading: boolean;
  updatedAt: Date | null;
}

/**
 * Polls `GET /me/notifications` for the signed-in buyer, so that the notifications and the badge are
 * up to date without reloading the page. One request at a time: the next one is scheduled only when the
 * previous one has ended. Nothing runs while the tab is hidden (`document.visibilityState`) or
 * once the provider is unmounted. When `enabled` is false (visitor, seller, admin) no request is sent.
 * Mount it with a `key` tied to the user, so that one user never sees the data of another.
 */
export function NotificationsProvider({ enabled, children }: { enabled: boolean; children: ReactNode }) {
  const api = useApi();
  const [state, setState] = useState<FeedState>({ page: null, message: null, loading: false, updatedAt: null });
  const pollRef = useRef<() => void>(() => {});

  useEffect(() => {
    if (!enabled) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let controller: AbortController | null = null;
    let disposed = false;
    const visible = () => document.visibilityState === "visible";

    function schedule() {
      clearTimeout(timer);
      if (!disposed && visible()) timer = setTimeout(() => void poll(), NOTIFICATIONS_POLL_MS);
    }

    async function poll() {
      if (disposed || controller || !visible()) return;
      clearTimeout(timer);
      const current = new AbortController();
      controller = current;
      setState((s) => ({ ...s, loading: true }));
      try {
        const page = await api.notification<Page<AppNotification>>(
          `/me/notifications?limit=${NOTIFICATIONS_PAGE_SIZE}&offset=0`,
          { signal: current.signal },
        );
        if (!current.signal.aborted) setState({ page, message: null, loading: false, updatedAt: new Date() });
      } catch (error) {
        // Last data kept: a failed update does not empty the list.
        if (!current.signal.aborted) setState((s) => ({ ...s, message: describeError(error), loading: false }));
      } finally {
        if (controller === current) controller = null;
        if (!current.signal.aborted) schedule();
      }
    }

    function onVisibilityChange() {
      if (visible()) {
        void poll();
      } else {
        clearTimeout(timer);
        controller?.abort();
        controller = null;
        setState((s) => (s.loading ? { ...s, loading: false } : s));
      }
    }

    pollRef.current = () => void poll();
    document.addEventListener("visibilitychange", onVisibilityChange);
    void poll();
    return () => {
      disposed = true;
      clearTimeout(timer);
      controller?.abort();
      document.removeEventListener("visibilitychange", onVisibilityChange);
      pollRef.current = () => {};
    };
  }, [api, enabled]);

  const refresh = useCallback(() => pollRef.current(), []);
  const value = useMemo<NotificationsFeed>(
    () => (enabled ? { ...state, total: state.page?.total ?? null, refresh } : EMPTY),
    [enabled, state, refresh],
  );
  return <FeedContext.Provider value={value}>{children}</FeedContext.Provider>;
}

const VISUALLY_HIDDEN = {
  position: "absolute",
  width: 1,
  height: 1,
  overflow: "hidden",
  clipPath: "inset(50%)",
  whiteSpace: "nowrap",
} as const;

/** Count pill for the navigation: nothing when there is no notification (or for a non-buyer). */
export function NotificationBadge() {
  const { total } = useNotifications();
  if (!total) return null;
  return (
    <>
      <Box
        component="span"
        aria-hidden="true"
        sx={{
          ml: 1,
          minWidth: 22,
          height: 22,
          px: 0.75,
          borderRadius: 11,
          display: "inline-grid",
          placeItems: "center",
          fontSize: 12,
          fontWeight: 700,
          lineHeight: 1,
          bgcolor: "secondary.main",
          color: "secondary.contrastText",
        }}
      >
        {total > 99 ? "99+" : total}
      </Box>
      <Box component="span" sx={VISUALLY_HIDDEN}>
        {`(${total} notification${total > 1 ? "s" : ""})`}
      </Box>
    </>
  );
}
