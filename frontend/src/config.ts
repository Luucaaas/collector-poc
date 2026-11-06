import { createContext, useContext } from "react";

/** Configuration d'exécution, lue dans /config.json avant le démarrage de l'application. */
export interface AppConfig {
  authority: string;
  clientId: string;
  catalogApiUrl: string;
  notificationApiUrl: string;
}

export class ConfigError extends Error {}

const URL_FIELDS = ["authority", "catalogApiUrl", "notificationApiUrl"] as const;

function isHttpUrl(value: unknown): value is string {
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

/** Valide un objet JSON déjà décodé ; les adresses perdent leur éventuelle barre finale. */
export function parseConfig(raw: unknown): AppConfig {
  if (typeof raw !== "object" || raw === null) {
    throw new ConfigError("Le fichier de configuration /config.json est invalide : objet JSON attendu.");
  }
  const data = raw as Record<string, unknown>;
  if (typeof data.clientId !== "string" || data.clientId.trim() === "") {
    throw new ConfigError("Configuration invalide : « clientId » est manquant.");
  }
  for (const field of URL_FIELDS) {
    if (!isHttpUrl(data[field])) {
      throw new ConfigError(`Configuration invalide : « ${field} » doit être une adresse http(s) valide.`);
    }
  }
  const strip = (value: unknown) => (value as string).replace(/\/+$/, "");
  return {
    authority: strip(data.authority),
    clientId: data.clientId,
    catalogApiUrl: strip(data.catalogApiUrl),
    notificationApiUrl: strip(data.notificationApiUrl),
  };
}

/** Charge /config.json ; toute erreur devient une ConfigError au message lisible. */
export async function loadConfig(fetchImpl: typeof fetch = fetch): Promise<AppConfig> {
  let response: Response;
  try {
    response = await fetchImpl("/config.json", { cache: "no-store" });
  } catch {
    throw new ConfigError("Impossible de charger le fichier de configuration /config.json.");
  }
  if (!response.ok) {
    throw new ConfigError(
      `Fichier de configuration /config.json introuvable (HTTP ${response.status}).`,
    );
  }
  let raw: unknown;
  try {
    raw = await response.json();
  } catch {
    throw new ConfigError("Le fichier de configuration /config.json n'est pas un JSON valide.");
  }
  return parseConfig(raw);
}

export const ConfigContext = createContext<AppConfig | null>(null);

export function useConfig(): AppConfig {
  const config = useContext(ConfigContext);
  if (config === null) throw new Error("useConfig doit être utilisé sous ConfigContext.Provider");
  return config;
}
