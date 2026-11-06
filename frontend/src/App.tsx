import { Route, Routes } from "react-router";
import { RequireRole } from "./auth/RequireRole";
import { Layout } from "./components/Layout";
import { CataloguePage } from "./pages/CataloguePage";
import { Placeholder } from "./pages/Placeholder";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CataloguePage />} />
        <Route
          path="vendre"
          element={
            <RequireRole role="seller">
              <Placeholder title="Vendre" />
            </RequireRole>
          }
        />
        <Route
          path="centres-interet"
          element={
            <RequireRole role="buyer">
              <Placeholder title="Mes centres d'intérêt" />
            </RequireRole>
          }
        />
        <Route
          path="categories"
          element={
            <RequireRole role="admin">
              <Placeholder title="Catégories" />
            </RequireRole>
          }
        />
        <Route path="*" element={<Placeholder title="Page introuvable" />} />
      </Route>
    </Routes>
  );
}
