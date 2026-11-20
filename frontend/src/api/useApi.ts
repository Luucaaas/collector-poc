import { useMemo } from "react";
import { useAuth } from "react-oidc-context";
import { useConfig } from "../config";
import { apiRequest } from "./client";

type Call = <T>(path: string, options?: { method?: "GET" | "POST" | "PUT"; body?: unknown; signal?: AbortSignal }) => Promise<T>;

/** Calls to the two APIs, with the signed-in user's token (or without a token when signed out). */
export function useApi(): { catalog: Call; notification: Call } {
  const config = useConfig();
  const token = useAuth().user?.access_token ?? null;
  return useMemo(() => {
    const bind =
      (baseUrl: string): Call =>
      (path, options) =>
        apiRequest({ baseUrl, path, token, ...options });
    return { catalog: bind(config.catalogApiUrl), notification: bind(config.notificationApiUrl) };
  }, [config, token]);
}
