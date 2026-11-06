import { afterEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "./client";
import { ApiError, describeError } from "./errors";

const BASE = "https://api.test/catalog/api/v1";

function mockFetch(response: Response | Error) {
  const fn = vi.fn(() => (response instanceof Error ? Promise.reject(response) : Promise.resolve(response)));
  vi.stubGlobal("fetch", fn);
  return fn;
}

function problem(status: number, body: object) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/problem+json" },
  });
}

async function failure(response: Response | Error): Promise<ApiError> {
  mockFetch(response);
  try {
    await apiRequest({ baseUrl: BASE, path: "/x" });
  } catch (error) {
    return error as ApiError;
  }
  throw new Error("une erreur était attendue");
}

afterEach(() => vi.unstubAllGlobals());

describe("apiRequest", () => {
  it("ajoute l'en-tête Bearer quand un jeton est fourni", async () => {
    const fetchMock = mockFetch(Response.json({ items: [], total: 0 }));
    await apiRequest({ baseUrl: BASE, path: "/articles", token: "abc" });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${BASE}/articles`);
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer abc");
  });

  it("n'ajoute pas Authorization sans jeton", async () => {
    const fetchMock = mockFetch(Response.json({}));
    await apiRequest({ baseUrl: BASE, path: "/categories" });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.headers).not.toHaveProperty("Authorization");
  });

  it("envoie un X-Request-ID conforme au contrat, différent à chaque appel", async () => {
    const fetchMock = mockFetch(Response.json({}));
    await apiRequest({ baseUrl: BASE, path: "/a" });
    fetchMock.mockImplementation(() => Promise.resolve(Response.json({})));
    await apiRequest({ baseUrl: BASE, path: "/b" });
    const ids = fetchMock.mock.calls.map(
      (call) => ((call as unknown as [string, RequestInit])[1].headers as Record<string, string>)["X-Request-ID"],
    );
    for (const id of ids) expect(id).toMatch(/^[A-Za-z0-9._-]{1,128}$/);
    expect(ids[0]).not.toBe(ids[1]);
  });

  it("envoie le corps JSON avec son Content-Type", async () => {
    const fetchMock = mockFetch(Response.json({}));
    await apiRequest({ baseUrl: BASE, path: "/p", method: "PUT", body: { price: "95.00" } });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.method).toBe("PUT");
    expect(init.body).toBe('{"price":"95.00"}');
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
  });

  it("lit une erreur RFC 9457 et expose statut, codes et corrélation", async () => {
    const error = await failure(
      problem(422, {
        title: "Données invalides",
        status: 422,
        errors: [{ field: "title", code: "CONTACT_EMAIL" }],
        correlation_id: "abc-123",
      }),
    );
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
    expect(error.codes).toEqual(["CONTACT_EMAIL"]);
    expect(error.correlationId).toBe("abc-123");
  });

  it("transforme une panne réseau en ApiError de statut 0", async () => {
    const error = await failure(new TypeError("Failed to fetch"));
    expect(error.status).toBe(0);
    expect(describeError(error)).toMatch(/Impossible de joindre le serveur/);
  });

  it("tolère un corps d'erreur qui n'est pas du JSON", async () => {
    const error = await failure(new Response("<html>Bad Gateway</html>", { status: 502 }));
    expect(error.status).toBe(502);
    expect(describeError(error)).toMatch(/erreur/);
  });
});

describe("describeError", () => {
  const msg = (status: number, errors?: { field?: string; code?: string }[]) =>
    describeError(new ApiError(status, { status, errors }));

  it.each([
    ["CONTACT_EMAIL", /adresse email/],
    ["CONTACT_PHONE", /numéro de téléphone/],
    ["SHOP_NOT_FOUND", /boutique/],
    ["CATEGORY_NOT_FOUND", /catégorie/],
    ["TOO_MANY_CATEGORIES", /20 catégories/],
  ])("traduit le code métier %s", (code, expected) => {
    expect(msg(422, [{ field: "x", code }])).toMatch(expected);
  });

  it("décrit une validation générique champ par champ", () => {
    expect(msg(422, [{ field: "price", code: "VALUE_ERROR" }])).toBe(
      "Les données saisies sont invalides : price (valeur invalide).",
    );
  });

  it("traduit 401, 403, 404, 409 et 5xx", () => {
    expect(msg(401)).toMatch(/session a expiré/);
    expect(msg(403)).toMatch(/pas le droit/);
    expect(msg(404)).toMatch(/introuvable/);
    expect(msg(409)).toMatch(/conflit/);
    expect(msg(409, [{ code: "NAME_ALREADY_USED" }])).toMatch(/déjà utilisé/);
    expect(msg(500)).toMatch(/Réessayez plus tard/);
  });

  it("ignore un code inconnu ou hérité d'Object (constructor, toString)", () => {
    expect(msg(422, [{ field: "x", code: "constructor" }])).toBe(
      "Les données saisies sont invalides : x (valeur invalide).",
    );
    expect(msg(409, [{ code: "toString" }])).toMatch(/conflit/);
  });
});
