import { describe, expect, it } from "vitest";
import { palette, theme } from "./theme";
import { tileColor } from "./components/ItemCard";

function luminance(hex: string): number {
  const channels = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const [r, g, b] = channels.map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

const WHITE = "#ffffff";

describe("theme: WCAG AA contrast (4.5:1 for text)", () => {
  it("body and secondary text on the page and card backgrounds", () => {
    for (const text of [palette.textPrimary, palette.textSecondary]) {
      expect(contrast(text, palette.background)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(text, palette.paper)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("white text on the header, buttons, badge and every severity of a filled alert (toast)", () => {
    const p = theme.palette;
    for (const colour of [p.primary.main, p.secondary.main, p.success.main, p.error.main, p.warning.main, p.info.main]) {
      expect(contrast(WHITE, colour)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("white initials on every illustration tile colour", () => {
    for (const seed of ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]) {
      expect(contrast(WHITE, tileColor(seed))).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("links and primary text colour on the page background", () => {
    expect(contrast(palette.primary, palette.background)).toBeGreaterThanOrEqual(4.5);
  });

  it("the off state of a switch is visible against the card (3:1 for components)", () => {
    const track = (theme.components?.MuiSwitch?.styleOverrides?.track as { backgroundColor: string }).backgroundColor;
    expect(contrast(track, palette.paper)).toBeGreaterThanOrEqual(3);
  });

  it("the on state of a switch has a primary track and a white thumb", () => {
    const base = theme.components?.MuiSwitch?.styleOverrides?.switchBase as Record<string, Record<string, unknown>>;
    expect(base["&.Mui-checked + .MuiSwitch-track"]).toMatchObject({ backgroundColor: palette.primary, opacity: 1 });
    expect(base["&.Mui-checked"]).toMatchObject({ color: "#ffffff" });
    expect(contrast(palette.primary, palette.paper)).toBeGreaterThanOrEqual(3);
  });
});

describe("theme: focus and motion", () => {
  it("defines a visible focus outline and honours reduced motion", () => {
    const rules = theme.components?.MuiCssBaseline?.styleOverrides as Record<string, unknown>;
    expect(rules[":focus-visible"]).toMatchObject({ outline: expect.stringContaining("3px solid") });
    expect(Object.keys(rules)).toContain("@media (prefers-reduced-motion: reduce)");
  });
});
