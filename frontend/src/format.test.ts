import { describe, expect, it } from "vitest";
import { formatMoney, formatTime } from "./format";

describe("formatMoney", () => {
  it("formats a decimal string as euros", () => {
    expect(formatMoney("120.00").replace(/\s/g, " ")).toBe("120,00 €");
    expect(formatMoney("8.5").replace(/\s/g, " ")).toBe("8,50 €");
    expect(formatMoney("1234.00").replace(/\s/g, " ")).toBe("1 234,00 €");
  });
});

describe("formatTime", () => {
  it("formats a time of day in French, with seconds", () => {
    expect(formatTime(new Date(2026, 10, 21, 9, 5, 7))).toBe("09:05:07");
  });
});
