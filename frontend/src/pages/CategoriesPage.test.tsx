import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { json, problem, renderWithToasts, stubApi } from "../test/api";
import { CategoriesPage } from "./CategoriesPage";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: { access_token: "jeton-admin" } }) }));
afterEach(() => vi.unstubAllGlobals());

const cat = (id: string, name: string) => ({ id, name, slug: name.toLowerCase(), created_at: "2026-11-01T00:00:00Z" });

describe("CategoriesPage", () => {
  it("creates a category and updates the list", async () => {
    let list = [cat("c1", "Cartes")];
    const calls = stubApi(({ method }) => {
      if (method === "POST") {
        list = [...list, cat("c2", "Figurines")];
        return json(cat("c2", "Figurines"), 201);
      }
      return json({ items: list, total: list.length });
    });
    renderWithToasts(<CategoriesPage />);
    expect(await screen.findByText("Cartes")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "Figurines");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));

    expect(await screen.findByText("Catégorie « Figurines » créée.")).toBeInTheDocument();
    expect(await screen.findByText("figurines")).toBeInTheDocument();
    expect(calls.find((c) => c.method === "POST")).toMatchObject({ path: "/categories", body: { name: "Figurines" } });
  });

  it("shows the French refusal of an already used name (409)", async () => {
    stubApi(({ method }) =>
      method === "POST"
        ? problem(409, { errors: [{ code: "NAME_ALREADY_USED" }] })
        : json({ items: [cat("c1", "Cartes")], total: 1 }),
    );
    renderWithToasts(<CategoriesPage />);
    await screen.findByText("Cartes");
    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "cartes");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    expect(await screen.findByText(/déjà utilisé/)).toBeInTheDocument();
  });

  it("shows an invalid name (422 NAME_INVALID) and the empty list", async () => {
    stubApi(({ method }) =>
      method === "POST"
        ? problem(422, { errors: [{ field: "name", code: "NAME_INVALID" }] })
        : json({ items: [], total: 0 }),
    );
    renderWithToasts(<CategoriesPage />);
    expect(await screen.findByText("Aucune catégorie pour le moment.")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "!!");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    expect(await screen.findByText(/nom est invalide/)).toBeInTheDocument();
  });

  it("rejects a one-character name in the browser, without calling the API", async () => {
    const calls = stubApi(() => json({ items: [], total: 0 }));
    renderWithToasts(<CategoriesPage />);
    await screen.findByText("Aucune catégorie pour le moment.");
    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "A");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    expect(await screen.findByText("Le nom doit contenir entre 2 et 60 caractères.")).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });

  it("checks the name live: counter, error after leaving the field, no error while typing the first letters", async () => {
    stubApi(() => json({ items: [], total: 0 }));
    renderWithToasts(<CategoriesPage />);
    await screen.findByText("Aucune catégorie pour le moment.");
    const field = screen.getByLabelText(/Nom de la catégorie/);
    expect(screen.getByText("Entre 2 et 60 caractères (0/60).")).toBeInTheDocument();
    await userEvent.type(field, "A");
    expect(screen.getByText("Entre 2 et 60 caractères (1/60).")).toBeInTheDocument();
    expect(field).not.toHaveAttribute("aria-invalid", "true");
    await userEvent.tab();
    expect(await screen.findByText("Le nom doit contenir entre 2 et 60 caractères.")).toBeInTheDocument();
    expect(field).toHaveAttribute("aria-invalid", "true");
    expect(field).toHaveAccessibleDescription("Le nom doit contenir entre 2 et 60 caractères.");
    await userEvent.type(field, "b");
    expect(screen.queryByText("Le nom doit contenir entre 2 et 60 caractères.")).not.toBeInTheDocument();
  });

  it("warns, without blocking, when the name is already used (case-insensitive)", async () => {
    const calls = stubApi(({ method }) =>
      method === "POST" ? problem(409, { errors: [{ code: "NAME_ALREADY_USED" }] }) : json({ items: [cat("c1", "Cartes")], total: 1 }),
    );
    renderWithToasts(<CategoriesPage />);
    await screen.findByText("Cartes");
    await userEvent.type(screen.getByLabelText(/Nom de la catégorie/), "CARTES");
    expect(screen.getByText(/porte déjà ce nom/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    expect(await screen.findByText(/déjà utilisé/)).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST")).toBe(true);
  });

  it("lists the categories as cards under a heading with the count, and clears the form after creation", async () => {
    stubApi(({ method }) =>
      method === "POST" ? json(cat("c2", "Figurines"), 201) : json({ items: [cat("c1", "Cartes")], total: 1 }),
    );
    renderWithToasts(<CategoriesPage />);
    expect(await screen.findByRole("heading", { level: 2, name: "Catégories existantes (1)" })).toBeInTheDocument();
    const list = screen.getByRole("list", { name: "Liste des catégories" });
    expect(within(list).getByRole("heading", { level: 3, name: "Cartes" })).toBeInTheDocument();
    expect(within(list).getByText(/Créée le/)).toBeInTheDocument();
    const field = screen.getByLabelText(/Nom de la catégorie/);
    await userEvent.type(field, "Figurines");
    await userEvent.click(screen.getByRole("button", { name: "Créer la catégorie" }));
    await screen.findByText("Catégorie « Figurines » créée.");
    expect(field).toHaveValue("");
    expect(field).not.toHaveAttribute("aria-invalid", "true");
  });

  it("shows an error message and no list when loading fails", async () => {
    stubApi(() => problem(500));
    renderWithToasts(<CategoriesPage />);
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Liste des catégories" })).not.toBeInTheDocument();
  });

  it("has a single h1, a named form and a loading placeholder", async () => {
    stubApi(() => json({ items: [], total: 0 }));
    renderWithToasts(<CategoriesPage />);
    expect(screen.getByRole("status", { name: "Chargement des catégories" })).toBeInTheDocument();
    await screen.findByText("Aucune catégorie pour le moment.");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("form", { name: "Créer une catégorie" })).toBeInTheDocument();
  });
});
