import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { useAuth } from "react-oidc-context";
import type { Article } from "../api/types";

interface RejectedArticles {
  rejected: Article[];
  add: (article: Article) => void;
}

// Outside a provider (isolated tests of a page), nothing is kept.
const RejectedContext = createContext<RejectedArticles>({ rejected: [], add: () => {} });

/** Articles rejected by the automatic check during this visit (never stored in the browser). */
export const useRejectedArticles = () => useContext(RejectedContext);

/**
 * Lives above the routes, so the list survives navigation inside the application. It is tied to
 * the signed-in user: when the user signs out or changes, the list is empty again.
 */
export function RejectedArticlesProvider({ children }: { children: ReactNode }) {
  const userId = useAuth().user?.profile?.sub ?? null;
  const [state, setState] = useState<{ owner: string | null; items: Article[] }>({ owner: userId, items: [] });
  // Signing out or changing user empties the list (state adjusted during render, React's documented pattern).
  if (state.owner !== userId) setState({ owner: userId, items: [] });
  const rejected = state.items;

  const add = useCallback(
    (article: Article) =>
      setState((previous) => ({
        owner: userId,
        items: [article, ...(previous.owner === userId ? previous.items : []).filter((a) => a.id !== article.id)],
      })),
    [userId],
  );
  const value = useMemo(() => ({ rejected, add }), [rejected, add]);
  return <RejectedContext.Provider value={value}>{children}</RejectedContext.Provider>;
}
