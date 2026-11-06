import { useEffect, useState } from "react";
import { describeError } from "./errors";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: T };

/** Exécute `load` à chaque changement de `deps` et annule la requête précédente. */
export function useAsync<T>(load: (signal: AbortSignal) => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading" });
  useEffect(() => {
    const controller = new AbortController();
    // Chargement lancé au montage ou au changement de dépendances : état « en cours » d'abord.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState({ status: "loading" });
    load(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setState({ status: "success", data });
      },
      (error: unknown) => {
        if (!controller.signal.aborted) setState({ status: "error", message: describeError(error) });
      },
    );
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}
