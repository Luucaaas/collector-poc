import { ThemeProvider } from "@mui/material/styles";
import { Pagination } from "@mui/material";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { lazy, Suspense } from "react";
import { describe, expect, it, vi } from "vitest";
import { theme } from "../theme";
import { ErrorBoundary } from "./ErrorBoundary";
import { EmptyState } from "./EmptyState";
import { initials, ItemCard, tileColor } from "./ItemCard";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { PageHeader } from "./PageHeader";
import { ToastProvider, useToast } from "./Toast";

describe("PageHeader", () => {
  it("renders the only h1 and sets the document title", () => {
    render(<PageHeader title="Catalogue" subtitle="Tous les articles" />);
    expect(screen.getByRole("heading", { level: 1, name: "Catalogue" })).toBeInTheDocument();
    expect(screen.getByText("Tous les articles")).toBeInTheDocument();
    expect(document.title).toBe("Catalogue · Collector.shop");
  });
});

describe("EmptyState and LoadingSkeleton", () => {
  it("shows title, description and action", () => {
    render(<EmptyState title="Rien ici" description="Revenez plus tard" action={<button>Agir</button>} />);
    expect(screen.getByText("Rien ici")).toBeInTheDocument();
    expect(screen.getByText("Revenez plus tard")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Agir" })).toBeInTheDocument();
  });

  it("exposes a labelled busy status", () => {
    render(<LoadingSkeleton label="Chargement des articles" />);
    expect(screen.getByRole("status", { name: "Chargement des articles" })).toHaveAttribute("aria-busy", "true");
  });
});

describe("ItemCard", () => {
  it("derives stable initials and colour from the text", () => {
    expect(initials("timbre rare")).toBe("TR");
    expect(initials("Vendre")).toBe("V");
    expect(tileColor("abc")).toBe(tileColor("abc"));
  });

  it("links the whole card when `to` is given", () => {
    render(
      <MemoryRouter>
        <ItemCard title="Timbre" to="/catalogue">
          Détail
        </ItemCard>
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: /Timbre/ })).toHaveAttribute("href", "/catalogue");
  });
});

describe("Toast", () => {
  function Trigger() {
    const notify = useToast();
    return <button onClick={() => notify("Enregistré", "success")}>Go</button>;
  }

  it("shows a message announced to assistive technology, and can be closed", async () => {
    render(
      <ThemeProvider theme={theme}>
        <ToastProvider>
          <Trigger />
        </ToastProvider>
      </ThemeProvider>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Enregistré");
    await act(async () => userEvent.click(screen.getByRole("button", { name: "Fermer" })));
  });

  it("is a no-op outside a provider", async () => {
    render(<Trigger />);
    await userEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("French locale of MUI components", () => {
  it("labels the pagination in French", () => {
    render(
      <ThemeProvider theme={theme}>
        <Pagination count={3} />
      </ThemeProvider>,
    );
    expect(screen.getByRole("button", { name: "Aller à la page 2" })).toBeInTheDocument();
  });
});

describe("ErrorBoundary", () => {
  it("shows a French message and a reload button when a lazy chunk fails to load", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const Broken = lazy(() => Promise.reject(new Error("Failed to fetch dynamically imported module")));
    render(
      <ErrorBoundary>
        <Suspense fallback={<LoadingSkeleton />}>
          <Broken />
        </Suspense>
      </ErrorBoundary>,
    );
    expect(await screen.findByText(/n'a pas pu être chargée/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Recharger la page" })).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
