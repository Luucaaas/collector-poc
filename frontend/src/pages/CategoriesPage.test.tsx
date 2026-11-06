import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { json, problem, renderWithConfig, stubApi } from "../test/api";
import { CategoriesPage } from "./CategoriesPage";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: { access_token: "jeton-admin" } }) }));
afterEach(() => vi.unstubAllGlobals());

const cat = (id: string, name: string) => ({ id, name, slug: name.toLowerCase(), created_at: "2026-11-01T00:00:00Z" });

describe("CategoriesPage", () => {
  it("crée une catégorie et met la liste à jour", async () => {
    let list = [cat("c1", "Cartes")];
    const calls = stubApi(({ method }) => {
      if (method === "POST") {
        list = [...list, cat("c2", "Figurines")];
        return json(cat("c2", "Figurines"), 201);
      }
      return json({ items: list, total: list.length });
    });
    renderWithConfig(<CategoriesPage />);
    expect(await screen.findByText("Cartes")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "Figurines");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));

    expect(await screen.findByText("Catégorie « Figurines » créée.")).toBeInTheDocument();
    expect(await screen.findByText("figurines")).toBeInTheDocument();
    expect(calls.find((c) => c.method === "POST")).toMatchObject({ path: "/categories", body: { name: "Figurines" } });
  });

  it("affiche en français le refus d'un nom déjà utilisé (409)", async () => {
    stubApi(({ method }) =>
      method === "POST"
        ? problem(409, { errors: [{ code: "NAME_ALREADY_USED" }] })
        : json({ items: [cat("c1", "Cartes")], total: 1 }),
    );
    renderWithConfig(<CategoriesPage />);
    await screen.findByText("Cartes");
    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "cartes");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    expect(await screen.findByText(/déjà utilisé/)).toBeInTheDocument();
  });

  it("affiche un nom invalide (422 NAME_INVALID) et la liste vide", async () => {
    stubApi(({ method }) =>
      method === "POST"
        ? problem(422, { errors: [{ field: "name", code: "NAME_INVALID" }] })
        : json({ items: [], total: 0 }),
    );
    renderWithConfig(<CategoriesPage />);
    expect(await screen.findByText("Aucune catégorie pour le moment.")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "!!");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    expect(await screen.findByText(/nom est invalide/)).toBeInTheDocument();
  });

  it("refuse côté navigateur un nom d'un seul caractère, sans appeler l'API", async () => {
    const calls = stubApi(() => json({ items: [], total: 0 }));
    renderWithConfig(<CategoriesPage />);
    await screen.findByText("Aucune catégorie pour le moment.");
    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "A");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    expect(await screen.findByText("Le nom doit contenir entre 2 et 60 caractères.")).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });
});
