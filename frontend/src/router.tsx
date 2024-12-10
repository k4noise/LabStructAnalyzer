import Nav from "./components/Nav/Nav";
import { Outlet, createBrowserRouter } from "react-router";
import Templates from "./pages/Templates/Templates";
import { Template } from "./pages/Template/Template";

const router = createBrowserRouter([
  {
    element: (
      <>
        <Nav />
        <div>
          <Outlet />
        </div>
      </>
    ),
    children: [
      {
        path: "/templates",
        element: <Templates />,
      },
      {
        path: "/template",
        element: <Template />,
      },
    ],
  },
]);

export default router;
