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
    // The default warning and info colours give 3.1:1 and 3.9:1 under the white text of a filled alert
    // (toast): these two are darker, so that every toast reaches 4.5:1.
    warning: { main: "#b45309" },
    info: { main: "#0b5cad" },
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
    // Switch: the default off track (black at 38 %, #9e9e9e) has 2.7:1 against the card, and the on track is
    // a pale primary. Off: grey track at 4.8:1. On: full primary track with a white thumb. Plus a focus ring.
    MuiSwitch: {
      styleOverrides: {
        track: { backgroundColor: "#6b7280", opacity: 1 },
        // The real input is invisible: the focus ring goes on the thumb's holder.
        switchBase: {
          "&.Mui-checked": { color: "#ffffff" },
          "&.Mui-checked + .MuiSwitch-track": { backgroundColor: palette.primary, opacity: 1 },
          "&.Mui-focusVisible": { outline: `3px solid ${palette.primary}`, outlineOffset: -3, borderRadius: "50%" },
        },
      },
    },
    MuiCheckbox: {
      styleOverrides: {
        root: { borderRadius: 8, "&.Mui-focusVisible": { outline: `3px solid ${palette.primary}`, outlineOffset: 0 } },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        // Visible keyboard focus everywhere (MUI's default is a faint ripple); white on the dark header.
        ":focus-visible": { outline: `3px solid ${palette.primary}`, outlineOffset: 2 },
        // MUI buttons, chips and links set their own `outline: 0`: a more specific selector is needed.
        ".MuiButtonBase-root.Mui-focusVisible": { outline: `3px solid ${palette.primary}`, outlineOffset: 2 },
        "header :focus-visible, header .MuiButtonBase-root.Mui-focusVisible": { outlineColor: "#ffffff" },
        // The content area is focused by script after a navigation: no ring around the whole page.
        "main:focus-visible": { outline: "none" },
        // Respect the "reduce motion" system setting.
        "@media (prefers-reduced-motion: reduce)": {
          "*, *::before, *::after": {
            animationDuration: "0.01ms !important",
            animationIterationCount: "1 !important",
            transitionDuration: "0.01ms !important",
            scrollBehavior: "auto !important",
          },
        },
      },
    },
  },
  },
  frFR,
);
