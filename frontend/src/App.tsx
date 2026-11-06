import { Route, Routes } from "react-router";
import { RequireRole } from "./auth/RequireRole";
import { Layout } from "./components/Layout";
import { CataloguePage } from "./pages/CataloguePage";
import { CategoriesPage } from "./pages/CategoriesPage";
import { InterestsPage } from "./pages/InterestsPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { SellPage } from "./pages/SellPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CataloguePage />} />
        <Route
          path="vendre"
          element={
            <RequireRole role="seller">
              <SellPage />
            </RequireRole>
          }
        />
        <Route
          path="centres-interet"
          element={
            <RequireRole role="buyer">
              <InterestsPage />
            </RequireRole>
          }
        />
        <Route
          path="categories"
          element={
            <RequireRole role="admin">
              <CategoriesPage />
            </RequireRole>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
