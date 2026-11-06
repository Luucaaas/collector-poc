import { describe, expect, it } from "vitest";
import { normalizeAmount, validateFee, validatePrice } from "./money";

describe("money", () => {
  it("normalise en chaîne décimale à deux décimales", () => {
    expect(normalizeAmount("12")).toBe("12.00");
    expect(normalizeAmount("12,5")).toBe("12.50");
    expect(normalizeAmount(" 0.07 ")).toBe("0.07");
    expect(normalizeAmount("1.234")).toBeNull();
    expect(normalizeAmount("abc")).toBeNull();
    expect(normalizeAmount("-5")).toBeNull();
    expect(normalizeAmount("12345678")).toBeNull();
  });

  it("valide un prix strictement positif au plus égal à 1 000 000", () => {
    expect(validatePrice("120")).toEqual({ value: "120.00" });
    expect(validatePrice("0")).toEqual({ error: "Le prix doit être supérieur à 0." });
    expect(validatePrice("0,00")).toHaveProperty("error");
    expect(validatePrice("1000000")).toEqual({ value: "1000000.00" });
    expect(validatePrice("1000000,01")).toHaveProperty("error");
  });

  it("accepte des frais de port nuls", () => {
    expect(validateFee("0")).toEqual({ value: "0.00" });
    expect(validateFee("")).toHaveProperty("error");
  });
});
