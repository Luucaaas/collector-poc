import { describe, expect, it } from "vitest";
import { formatMoney } from "./format";

describe("formatMoney", () => {
  it("formate une chaîne décimale en euros", () => {
    expect(formatMoney("120.00").replace(/\s/g, " ")).toBe("120,00 €");
    expect(formatMoney("8.5").replace(/\s/g, " ")).toBe("8,50 €");
    expect(formatMoney("1234.00").replace(/\s/g, " ")).toBe("1 234,00 €");
  });
});
