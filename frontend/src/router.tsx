import Nav from "./components/Nav/Nav";
import { Outlet, createBrowserRouter } from "react-router";
import Templates from "./pages/Templates/Templates";
import ErrorPage from "./pages/ErrorPage/ErrorPage";
import { lazy, Suspense } from "react";
import Spinner from "./components/Spinner";
import { api } from "./utils/sendRequest";

const Template = lazy(() => import("./pages/Template/Template"));

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <div className="fixed left-1/2 top-1/3 -translate-x-1/2 -translate-y-1/3 ">
        <p className="text-5xl leading-tight">
          Для работы необходимо авторизоваться через LMS
        </p>
      </div>
    ),
  },
  {
    element: (
      <>
        <Suspense fallback={<Spinner />}>
          <Nav />
        </Suspense>
        <div>
          <Suspense fallback={<Spinner />}>
            <Outlet />
          </Suspense>
        </div>
      </>
    ),
    loader: async () => await api.get("/api/v1/users/me"),
    errorElement: <ErrorPage />,
    children: [
      {
        path: "/templates",
        element: <Templates />,
        loader: async () => await api.get("/api/v1/templates/all"),
      },
      {
        path: "/template/:id",
        element: <Template />,
        loader: async ({ params }) =>
          await api.get(`/api/v1/templates/${params.id}`),
      },
      {
        path: "*",
        element: <ErrorPage />,
      },
    ],
  },
]);

export default router;
