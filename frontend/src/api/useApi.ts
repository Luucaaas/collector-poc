import { useMemo } from "react";
import { useAuth } from "react-oidc-context";
import { useConfig } from "../config";
import { apiRequest } from "./client";

type Call = <T>(path: string, options?: { method?: "GET" | "POST" | "PUT"; body?: unknown; signal?: AbortSignal }) => Promise<T>;

/** Appels aux deux API, avec le jeton de l'utilisateur connecté (ou sans jeton s'il ne l'est pas). */
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
