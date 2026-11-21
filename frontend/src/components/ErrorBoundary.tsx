import { Alert, Button, Stack } from "@mui/material";
import { Component, type ReactNode } from "react";

/** Catches render errors, e.g. a lazy page chunk that fails to download (network cut, new deployment). */
export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <Stack spacing={2} sx={{ alignItems: "flex-start" }}>
        <Alert severity="error">
          Cette page n'a pas pu être chargée. Vérifiez votre connexion, puis rechargez la page.
        </Alert>
        <Button variant="contained" onClick={() => window.location.reload()}>
          Recharger la page
        </Button>
      </Stack>
    );
  }
}
