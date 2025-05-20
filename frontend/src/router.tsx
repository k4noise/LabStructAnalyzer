import { createBrowserRouter, redirect } from "react-router";
import Templates from "./pages/Templates/Templates";
import ErrorPage from "./pages/Error/Error";
import { lazy } from "react";
import { api } from "./utils/sendRequest";
import BaseLayout from "./components/BaseLayout/BaseLayout";
import { Reports } from "./pages/Reports/Reports";
import { ReportInfoDto } from "./model/reports";
import { TemplateModel } from "./model/template";
import Report from "./pages/Report/Report";

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
    element: <BaseLayout delay={300} />,
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
        path: "/template/:id/reports",
        element: <Reports />,
        loader: async ({ params }) =>
          await api.get(`/api/v1/templates/${params.id}/reports`),
      },
      {
        path: "/report/new/:templateId",
        loader: async ({ params }) => {
          const reportId = await api.post<{ id: string }>(
            `/api/v1/templates/${params.templateId}/reports`
          );
          return redirect(`/report/${reportId.data.id}`);
        },
      },
      {
        path: "/report/:id",
        element: <Report />,
        loader: async ({ params }) => {
          const report = await api.get<ReportInfoDto>(
            `/api/v1/reports/${params.id}`
          );
          const template = await api.get<TemplateModel>(
            `/api/v1/templates/${report.data.template_id}`
          );
          return { template: template.data, report: report.data };
        },
      },
      {
        path: "*",
        element: <ErrorPage />,
      },
    ],
  },
]);

export default router;
