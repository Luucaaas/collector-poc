import { useEffect, useMemo, useState } from "react";
import type { Shop } from "./types";
import { useApi } from "./useApi";

/**
 * Names of the given shops (public `GET /shops/{id}`, one call per distinct id).
 * A shop whose lookup fails is simply missing from the result: the caller shows a fallback.
 */
export function useShopNames(shopIds: string[]): Record<string, string> {
  const api = useApi();
  const key = useMemo(() => [...new Set(shopIds)].sort().join(","), [shopIds]);
  const [names, setNames] = useState<Record<string, string>>({});
  useEffect(() => {
    if (key === "") return;
    const controller = new AbortController();
    void Promise.allSettled(
      key.split(",").map((id) => api.catalog<Shop>(`/shops/${encodeURIComponent(id)}`, { signal: controller.signal })),
    ).then((results) => {
      if (controller.signal.aborted) return;
      const found: Record<string, string> = {};
      for (const result of results) if (result.status === "fulfilled") found[result.value.id] = result.value.name;
      setNames((previous) => ({ ...previous, ...found }));
    });
    return () => controller.abort();
  }, [api, key]);
  return names;
}
