import { frFR } from "@mui/material/locale";
import { createTheme } from "@mui/material/styles";

/**
 * Single visual identity of the application. Every colour pair used for text has a
 * contrast ratio of at least 4.5:1 (WCAG AA). No external font: system font stack, so the
 * Content-Security-Policy (`font-src` falls back to 'self') stays untouched.
 */
export const palette = {
  primary: "#1f3a5f",
  secondary: "#9a4a00",
  background: "#f6f5f1",
  paper: "#ffffff",
  textPrimary: "#1b1f27",
  textSecondary: "#4a5262",
};

const fontFamily = [
  "system-ui",
  "-apple-system",
  "Segoe UI",
  "Roboto",
  "Helvetica Neue",
  "Arial",
  "sans-serif",
].join(", ");

// frFR: French labels of the MUI components themselves (toast close button, pagination, ...).
export const theme = createTheme(
  {
  palette: {
    primary: { main: palette.primary },
    secondary: { main: palette.secondary },
    background: { default: palette.background, paper: palette.paper },
    text: { primary: palette.textPrimary, secondary: palette.textSecondary },
  },
  spacing: 8,
  shape: { borderRadius: 12 },
  typography: {
    fontFamily,
    h3: { fontWeight: 700, letterSpacing: "-0.02em" },
    h4: { fontWeight: 700, letterSpacing: "-0.01em" },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { textTransform: "none", fontWeight: 600 },
  },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiCard: { defaultProps: { variant: "outlined" } },
    MuiAppBar: { defaultProps: { elevation: 0 } },
  },
  },
  frFR,
);
