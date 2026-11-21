import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Article } from "../api/types";
import { RejectedArticlesProvider, useRejectedArticles } from "./RejectedArticles";

const auth: { sub: string | null } = { sub: "u1" };
vi.mock("react-oidc-context", () => ({
  useAuth: () => ({ user: auth.sub ? { profile: { sub: auth.sub } } : null }),
}));

const rejected = { id: "r1", title: "Annonce refusée", shop_id: "s1" } as Article;

function Probe() {
  const { rejected: items, add } = useRejectedArticles();
  return (
    <>
      <button onClick={() => add(rejected)}>ajouter</button>
      <ul>
        {items.map((a) => (
          <li key={a.id}>{a.title}</li>
        ))}
      </ul>
    </>
  );
}

/** Stands for the routes: the page below the provider is mounted and unmounted. */
function App() {
  const [visible, setVisible] = useState(true);
  return (
    <RejectedArticlesProvider>
      <button onClick={() => setVisible((v) => !v)}>basculer</button>
      {visible && <Probe />}
    </RejectedArticlesProvider>
  );
}

describe("RejectedArticlesProvider", () => {
  it("keeps the list when the page is left and visited again", async () => {
    auth.sub = "u1";
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "ajouter" }));
    expect(screen.getByText("Annonce refusée")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "basculer" }));
    await userEvent.click(screen.getByRole("button", { name: "basculer" }));
    expect(screen.getByText("Annonce refusée")).toBeInTheDocument();
  });

  it("empties the list when the user signs out or changes", async () => {
    auth.sub = "u1";
    const { rerender } = render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "ajouter" }));
    auth.sub = null;
    rerender(<App />);
    expect(screen.queryByText("Annonce refusée")).not.toBeInTheDocument();
    auth.sub = "u1";
    rerender(<App />);
    expect(screen.queryByText("Annonce refusée")).not.toBeInTheDocument();
    auth.sub = "u2";
    rerender(<App />);
    expect(screen.queryByText("Annonce refusée")).not.toBeInTheDocument();
  });
});
