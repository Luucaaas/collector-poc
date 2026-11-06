import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fakeAccessToken } from "../test/jwt";
import { RequireRole } from "./RequireRole";

const auth = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
vi.mock("react-oidc-context", () => ({ useAuth: () => auth.current }));

const signinRedirect = vi.fn(() => Promise.resolve());

function renderGuard(role: "seller" | "admin" = "seller") {
  return render(
    <MemoryRouter initialEntries={["/vendre"]}>
      <RequireRole role={role}>
        <p>contenu protégé</p>
      </RequireRole>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  signinRedirect.mockClear();
});

describe("RequireRole", () => {
  it("envoie vers la connexion un utilisateur non connecté", async () => {
    auth.current = { isLoading: false, isAuthenticated: false, signinRedirect };
    renderGuard();
    expect(screen.queryByText("contenu protégé")).not.toBeInTheDocument();
    await waitFor(() => expect(signinRedirect).toHaveBeenCalledWith({ state: { returnTo: "/vendre" } }));
  });

  it("affiche « accès refusé » à un utilisateur sans le rôle", () => {
    auth.current = {
      isLoading: false,
      isAuthenticated: true,
      signinRedirect,
      user: { access_token: fakeAccessToken(["buyer"]) },
    };
    renderGuard();
    expect(screen.getByText(/Accès refusé/)).toBeInTheDocument();
    expect(screen.queryByText("contenu protégé")).not.toBeInTheDocument();
    expect(signinRedirect).not.toHaveBeenCalled();
  });

  it("affiche le contenu à un utilisateur qui a le rôle", () => {
    auth.current = {
      isLoading: false,
      isAuthenticated: true,
      signinRedirect,
      user: { access_token: fakeAccessToken(["seller", "offline_access"]) },
    };
    renderGuard();
    expect(screen.getByText("contenu protégé")).toBeInTheDocument();
  });

  it("attend la fin du chargement avant de rediriger", () => {
    auth.current = { isLoading: true, isAuthenticated: false, signinRedirect };
    renderGuard();
    expect(signinRedirect).not.toHaveBeenCalled();
  });
});
