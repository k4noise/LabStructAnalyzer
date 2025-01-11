import { useLoaderData } from "react-router";
import { AllReportsInfo } from "../../model/reports";
import BackButtonComponent from "../../components/BackButtonComponent";
import { formatDate } from "../../utils/timestampFormatter";
import { Link } from "react-router";

export const Reports = () => {
  const { data: reportsInfo } = useLoaderData<{ data: AllReportsInfo }>();
  return (
    <div className="p-6">
      <BackButtonComponent positionClasses={"relative"} />
      <h1 className="text-3xl font-medium text-center mb-10">{`Отчеты "${reportsInfo.template_name}"`}</h1>

      {reportsInfo.reports.length ? (
        <table className="w-full border-collapse text-left break-words">
          <thead>
            <tr>
              <th className="p-3">Дата</th>
              <th className="p-3">ФИО</th>
              <th className="p-3">Отчет</th>
              <th className="p-3">Статус</th>
              <th className="p-3">Балл</th>
            </tr>
          </thead>
          <tbody>
            {reportsInfo.reports.map((report) => (
              <tr key={report.report_id}>
                <td className="p-3">{formatDate(report.date)}</td>
                <td className="p-3">{report.author_name}</td>
                <td className="p-3">
                  <Link to={`/report/${report.report_id}`} className="underline">Открыть</Link>
                </td>
                <td className="p-3">
                  <span
                    className={`px-2 py-1 border rounded-md text-base ${
                      report.status === "Проверен"
                        ? "border-green-600 text-green-600"
                        : report.status === "Отправлен на проверку"
                        ? "border-blue-600 text-blue-600"
                        : "border-yellow-600 text-yellow-600"
                    }`}
                  >
                    {report.status}
                  </span>
                </td>

                <td className="p-3">
                  {report.score
                    ? `${report.score}/${reportsInfo.max_score}`
                    : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="my-10">Нет доступных отчетов</p>
      )}
    </div>
  );
};
