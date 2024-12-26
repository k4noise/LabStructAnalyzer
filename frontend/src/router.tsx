import Nav from "./components/Nav/Nav";
import { Outlet, createBrowserRouter } from "react-router";
import Templates from "./pages/Templates/Templates";
import ErrorPage from "./pages/ErrorPage/ErrorPage";
import { lazy, Suspense } from "react";
import { getTemplate } from "./api/getTemplate";
import Spinner from "./components/Spinner";
import { getCourseName } from "./api/getCourseName";
import { getUser } from "./api/getUser";

const Template = lazy(() => import("./pages/Template/Template"));

const tryGetData = async (callback) => {
  const { data, error, description } = await callback();
  if (error) {
    throw new Error(JSON.stringify({ status: error, message: description }));
  }
  return data;
};

const router = createBrowserRouter([
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
    loader: async () => tryGetData(() => getUser()),
    errorElement: <ErrorPage />,
    children: [
      {
        path: "/templates",
        element: <Templates />,
        loader: async () => tryGetData(() => getCourseName()),
        errorElement: <ErrorPage />,
      },
      {
        path: "/template/:id",
        element: <Template />,
        loader: async ({ params }) => tryGetData(() => getTemplate(params.id)),
      },
      {
        path: "*",
        element: <ErrorPage />,
      },
    ],
  },
]);

export default router;
