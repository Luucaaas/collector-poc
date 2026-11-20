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
  it("sends a signed-out user to the sign-in", async () => {
    auth.current = { isLoading: false, isAuthenticated: false, signinRedirect };
    renderGuard();
    expect(screen.queryByText("contenu protégé")).not.toBeInTheDocument();
    await waitFor(() => expect(signinRedirect).toHaveBeenCalledWith({ state: { returnTo: "/vendre" } }));
  });

  it("shows \"access denied\" to a user without the role", () => {
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

  it("shows the content to a user who has the role", () => {
    auth.current = {
      isLoading: false,
      isAuthenticated: true,
      signinRedirect,
      user: { access_token: fakeAccessToken(["seller", "offline_access"]) },
    };
    renderGuard();
    expect(screen.getByText("contenu protégé")).toBeInTheDocument();
  });

  it("waits for loading to finish before redirecting", () => {
    auth.current = { isLoading: true, isAuthenticated: false, signinRedirect };
    renderGuard();
    expect(signinRedirect).not.toHaveBeenCalled();
  });
});
