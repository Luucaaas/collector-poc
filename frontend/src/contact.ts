/**
 * Live hint for the seller: does the text look like it contains an email address or a phone number?
 * It mirrors the method of `catalog-service` (contact.py), Unicode included (Python `\d` and `\w`
 * are Unicode-aware, so here they become `\p{Nd}` and `[\p{L}\p{N}_]` with the `u` flag), but it only
 * helps the user: the automatic check stays on the server, which has the last word (REJECTED
 * article, 422 for a shop).
 */
export const CONTACT_EMAIL = "CONTACT_EMAIL";
export const CONTACT_PHONE = "CONTACT_PHONE";

// Starts at the "@" (one valid character before it) to stay linear on long texts.
const EMAIL = /(?<=[\p{L}\p{N}_.+-])@[\p{L}\p{N}_-]+(?:\.[\p{L}\p{N}_-]+)+/u;
// Date dd.mm.yyyy: removed first, otherwise "05.11.2024 14h" would read as 10 digits starting with 0.
const DATE = /(?<!\p{Nd})\p{Nd}{1,2}([./-])\p{Nd}{1,2}\1(?:19|20)\p{Nd}{2}(?!\p{Nd})/gu;
const CANDIDATE = /\+?\(?\p{Nd}[\p{Nd}\s.\-/()]*\p{Nd}/gu;
const DIGIT = /^\p{Nd}$/u;
const codePoints = (text: string): string[] => Array.from(text);

function isNational(groups: string[]): boolean {
  const digits = codePoints(groups.join(""));
  const ends = new Set<number>();
  let total = 0;
  for (const group of groups) {
    total += codePoints(group).length;
    ends.add(total);
  }
  // A number starts at a group boundary with "0" then a digit other than 0, and ends at a boundary 10 digits later.
  return digits.some(
    (digit, start) =>
      digit === "0" &&
      start + 1 < digits.length &&
      digits[start + 1] !== "0" &&
      DIGIT.test(digits[start + 1]!) &&
      (start === 0 || ends.has(start)) &&
      ends.has(start + 10),
  );
}

function isPhone(candidate: string): boolean {
  const groups = candidate.match(/\p{Nd}+/gu) ?? [];
  const count = codePoints(groups.join("")).length;
  if (candidate.startsWith("+")) return count >= 9 && count <= 15;
  if (groups.join("").startsWith("00") && count - 2 >= 9 && count - 2 <= 15) return true;
  return isNational(groups);
}

/** Codes found in the texts: `CONTACT_EMAIL` then `CONTACT_PHONE`, without duplicates. */
export function detectContact(...texts: (string | undefined)[]): string[] {
  const present = texts.filter((t): t is string => !!t);
  const codes: string[] = [];
  if (present.some((t) => EMAIL.test(t))) codes.push(CONTACT_EMAIL);
  if (present.some((t) => (t.replace(DATE, " ").match(CANDIDATE) ?? []).some(isPhone))) codes.push(CONTACT_PHONE);
  return codes;
}
