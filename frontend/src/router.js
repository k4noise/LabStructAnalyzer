import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import Nav from "./components/Nav/Nav";
import { Outlet, createBrowserRouter } from "react-router";
import Templates from "./pages/Templates/Templates";
import { Template } from "./pages/Template/Template";
const router = createBrowserRouter([
    {
        element: (_jsxs(_Fragment, { children: [_jsx(Nav, {}), _jsx("div", { children: _jsx(Outlet, {}) })] })),
        children: [
            {
                path: "/templates",
                element: _jsx(Templates, {}),
            },
            {
                path: "/template",
                element: _jsx(Template, {}),
            },
        ],
    },
]);
export default router;
