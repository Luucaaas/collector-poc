import { Alert, Container, CssBaseline, CircularProgress } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { AuthProvider } from "react-oidc-context";
import { BrowserRouter, useNavigate } from "react-router";
import { App } from "./App";
import { createOidcSettings } from "./auth/oidc";
import { ConfigContext, loadConfig, type AppConfig } from "./config";

function AuthShell({ config }: { config: AppConfig }) {
  const navigate = useNavigate();
  const settings = useMemo(() => createOidcSettings(config, window.location.origin), [config]);
  return (
    <AuthProvider
      {...settings}
      // Retour de Keycloak : on remplace l'URL (sans `code` ni `state`) par la page demandée.
      onSigninCallback={(user) => {
        const state = user?.state as { returnTo?: string } | undefined;
        navigate(state?.returnTo ?? "/", { replace: true });
      }}
    >
      <App />
    </AuthProvider>
  );
}

/** Charge /config.json avant de démarrer l'authentification ; message clair en cas d'échec. */
export function Bootstrap() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConfig().then(setConfig, (e: unknown) =>
      setError(e instanceof Error ? e.message : "Configuration illisible."),
    );
  }, []);

  return (
    <>
      <CssBaseline />
      {error ? (
        <Container sx={{ py: 4 }}>
          <Alert severity="error">
            L'application ne peut pas démarrer. {error} Contactez l'administrateur.
          </Alert>
        </Container>
      ) : config ? (
        <ConfigContext.Provider value={config}>
          <BrowserRouter>
            <AuthShell config={config} />
          </BrowserRouter>
        </ConfigContext.Provider>
      ) : (
        <Container sx={{ py: 4 }}>
          <CircularProgress aria-label="Chargement" />
        </Container>
      )}
    </>
  );
}
