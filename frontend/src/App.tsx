import { lazy } from "react";
import { Route, Routes } from "react-router";
import { RequireRole } from "./auth/RequireRole";
import { Layout } from "./components/Layout";

// One chunk per page: the browser downloads a page only when it is visited.
const HomePage = lazy(() => import("./pages/HomePage").then((m) => ({ default: m.HomePage })));
const CataloguePage = lazy(() => import("./pages/CataloguePage").then((m) => ({ default: m.CataloguePage })));
const ArticleDetailPage = lazy(() => import("./pages/ArticleDetailPage").then((m) => ({ default: m.ArticleDetailPage })));
const CategoriesPage = lazy(() => import("./pages/CategoriesPage").then((m) => ({ default: m.CategoriesPage })));
const InterestsPage = lazy(() => import("./pages/InterestsPage").then((m) => ({ default: m.InterestsPage })));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })));
const SellPage = lazy(() => import("./pages/SellPage").then((m) => ({ default: m.SellPage })));

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="catalogue" element={<CataloguePage />} />
        <Route path="catalogue/:articleId" element={<ArticleDetailPage />} />
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
