import { describe, expect, it } from "vitest";
import { detectContact } from "./contact";

// Cases copied from services/catalog-service/tests/test_contact_slug.py: the front hint must agree with contact.py.
const EMAILS = [
  "écrivez-moi à jean.dupont@example.com pour négocier",
  "contact: a+b@sous.domaine.example.fr",
  "JEAN@EXAMPLE.COM",
];
const PHONES = [
  "appelez le 06 12 34 56 78 le soir",
  "0612345678",
  "06.12.34.56.78",
  "06-12-34-56-78",
  "01 23 45 67 89",
  "+33 6 12 34 56 78",
  "+33612345678",
  "+33 (0)6 12 34 56 78",
  "0033 6 12 34 56 78",
  "+44 7911 123456",
  "+1 415 555 0132",
  "+32 470 12 34 56",
  "00 49 151 23456789",
  "tel0612345678",
  "(0)6 12 34 56 78",
  "06/12/34/56/78",
  "Mon numéro : 06 12 34 56 78.",
  "WhatsApp +33 7 98 76 54 32 svp",
  "06 1234 5678",
  "0 6 12 34 56 78",
  "0 6 1 2 3 4 5 6 7 8",
  "06.12 34-56 78",
  "06 12 34 5678",
  "0612 34 56 78",
  "06 12 34 56 78",
  "06 12 34 56 78",
  "06  12 34 56 78",
  "Kenner 1979 06 12 34 56 78",
  "appelez le 06 12 34 56 78 2 fois",
  "Ligne directe : 01 23 45 67 89.",
  "+33(0)612345678",
];
const CLEAN = [
  "Boba Fett Kenner 1979",
  "Édité en 1979, réédité en 1983",
  "Prix 120,00 € frais de port 8,50 €",
  "Vendu 1 200 € à débattre",
  "Dimensions 30 x 20 x 10 cm, 450 g",
  "Référence SW-1234-5678 boîte d'origine",
  "Lot de 12 figurines, taille 42",
  "Date d'achat : 05/11/1999",
  "Code-barres 5010993456789",
  "Numéro de série 2024-11-03",
  "Note 4,5/5 sur 1 000 avis",
  "Publié le 05.11.2024 14h",
  "Plus de +12 000 000 exemplaires",
  "Le 01/02/2024 à 10h",
  "Série 00 1234 5678",
  "Vente du 05/11/2024 à 14:30, port 8,50 €",
  "Lot de 0612345 pièces",
  "Édition limitée 1995, 25 000 exemplaires numérotés",
  "Taille 42 - 44 EU",
  "Code EAN 3760123456789",
  "Tirage +50 000 exemplaires",
  "",
];

describe("detectContact (same cases as contact.py)", () => {
  it.each(EMAILS)("finds the email in %j", (text) => {
    expect(detectContact(text)).toEqual(["CONTACT_EMAIL"]);
  });

  it.each(PHONES)("finds the phone number in %j", (text) => {
    expect(detectContact(text)).toEqual(["CONTACT_PHONE"]);
  });

  it.each(CLEAN)("does not flag %j", (text) => {
    expect(detectContact(text)).toEqual([]);
  });

  it("reports both reasons, email first", () => {
    expect(detectContact("06 12 34 56 78 ou a@b.fr")).toEqual(["CONTACT_EMAIL", "CONTACT_PHONE"]);
  });

  it("leaves obfuscated forms out of scope, like the server", () => {
    expect(detectContact("zéro six douze trente-quatre", "jean arobase example point com")).toEqual([]);
    expect(detectContact("jean @ example.com")).toEqual([]);
  });

  it("reads a phone number written with non-ASCII digits", () => {
    expect(detectContact("Appelez le 0\u0666" + "12345678")).toEqual(["CONTACT_PHONE"]);
  });

  it.each(["José@example.com", "é@example.com", "mon@exämple.fr"])("reads the Unicode email %s", (text) => {
    expect(detectContact(text)).toEqual(["CONTACT_EMAIL"]);
  });

  it("handles several texts and missing values", () => {
    expect(detectContact("Titre propre", undefined, "mon@mail.fr")).toEqual(["CONTACT_EMAIL"]);
    expect(detectContact(undefined, "")).toEqual([]);
  });
});

// Worst cases of test_contact_performance.py: detection must stay linear on 100 000 characters.
const WORST_CASES: Record<string, string> = {
  letters: "a".repeat(100_000),
  "letters-dots": "a.".repeat(50_000),
  "letters-final-dot": "a".repeat(99_999) + ".",
  zeros: "0".repeat(100_000),
  "zeros-spaces": "0 ".repeat(50_000),
  "digits-spaces": "1 ".repeat(50_000) + "x",
  "plus-parentheses": "+(".repeat(50_000),
  "zero-one-spaces": "0 1 ".repeat(25_000),
  "at-signs": "a@".repeat(50_000),
  "domain-without-dot": "a@" + "b".repeat(100_000),
};

describe("detectContact performance", () => {
  it.each(Object.entries(WORST_CASES))("stays under 100 ms on %s", (_name, text) => {
    const start = performance.now();
    detectContact(text);
    expect(performance.now() - start).toBeLessThan(100);
  });
});
