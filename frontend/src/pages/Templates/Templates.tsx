import { Link, useLoaderData, useNavigate } from "react-router";
import Modal from "../../components/Modal/Modal";
import { useState, FormEvent, ChangeEvent } from "react";
import { api, extractMessage } from "../../utils/sendRequest";
import Button from "../../components/Button/Button";
import { TemplateCourseCollection } from "../../model/template";
import { Helmet } from "react-helmet";

const getStatusClass = (status: string | null): string => {
  const base =
    "text-base border px-2 py-1 border-solid rounded-xl border-2 select-none";
  switch (status) {
    case "Новый":
      return `${base} border-blue-600 text-blue-600`;
    case "Создан":
      return `${base} border-indigo-600 text-indigo-600`;
    case "Сохранен":
      return `${base} border-cyan-600 text-cyan-600`;
    case "Отправлен на проверку":
      return `${base} border-yellow-600 text-yellow-600`;
    case "Проверен":
      return `${base} border-green-600 text-green-600`;
    default:
      return `${base} dark:border-zinc-200 border-zinc-950`;
  }
};

interface TemplateItemProps {
  template: any;
  userRole: "teacher" | "assistant" | "student";
  onCreateReport?: (href: string) => void;
}

const TemplateItem = ({
  template,
  userRole,
  onCreateReport,
}: TemplateItemProps) => {
  const reports = template.embedded?.reports || [];

  const isTeacher = userRole === "teacher";
  const isAssistant = userRole === "assistant";
  const isStudent = userRole === "student";
  const showReportsButton =
    (isTeacher || isAssistant) && !!template.links?.get_reports;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        {isTeacher ? (
          <Link to={`/template/${template.id}`} className="underline">
            {template.name}
          </Link>
        ) : (
          <p>{template.name}</p>
        )}

        {showReportsButton && (
          <Link
            to={`/template/${template.id}/reports`}
            className="text-base border px-2 py-1 dark:border-zinc-200 border-zinc-950 border-solid rounded-xl border-2"
          >
            Все отчёты
          </Link>
        )}
      </div>

      {(isStudent || isAssistant) && (
        <div className="ml-4 flex flex-col gap-2">
          {reports.length > 0 ? (
            reports.map((report) => (
              <div key={report.report_id} className="flex items-center gap-4">
                <Link to={`/report/${report.report_id}`} className="underline">
                  {report.name || `Отчёт ${report.created_at}`}
                </Link>
                <span className={getStatusClass(report.status)}>
                  {report.status}
                </span>
              </div>
            ))
          ) : (
            <Button
              text="Создать отчёт"
              onClick={() =>
                onCreateReport?.(template.links?.create_report?.href)
              }
              classes="text-base border px-2 py-1 dark:border-zinc-200 border-zinc-950 border-solid rounded-xl border-2 w-fit"
            />
          )}
        </div>
      )}
    </div>
  );
};

const Templates = () => {
  const { data } = useLoaderData<{ data: TemplateCourseCollection }>();
  const navigate = useNavigate();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const isTeacher = !!data.links.add_template;
  const isAssistant = !isTeacher && !!data.links.get_reports;

  const userRole: "teacher" | "assistant" | "student" = isTeacher
    ? "teacher"
    : isAssistant
    ? "assistant"
    : "student";

  const title = `${
    isTeacher ? "Шаблоны и отчёты" : "Отчёты"
  } лабораторных работ курса ${data.course_name}`;

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file?.name.endsWith(".docx")) {
      setSelectedFile(file);
      setUploadError(null);
    } else {
      setSelectedFile(null);
      setUploadError("Поддерживается только .docx");
    }
  };

  const handleUploadTemplate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("template", selectedFile);

    try {
      setIsUploading(true);
      const response = await api.post("/api/v1/templates", formData);
      navigate(`/template/${response.data.id}`);
    } catch (error) {
      setUploadError(extractMessage(error.response));
    } finally {
      setIsUploading(false);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setUploadError(null);
    setSelectedFile(null);
  };

  const createReport = async (href: string) => {
    if (!href) return;
    try {
      const response = await api.post(href);
      navigate(`/report/${response.data.id}`);
    } catch (e) {
      console.error("Не удалось создать отчёт:", e);
    }
  };

  const templates = data.embedded.templates || [];

  return (
    <div className="mt-8">
      <Helmet>
        <title>{title}</title>
      </Helmet>

      <h2 className="text-3xl font-bold text-center mb-10">{title}</h2>

      {isTeacher && (
        <Button
          text="+ Добавить шаблон"
          onClick={() => setIsModalOpen(true)}
          classes="mb-6"
        />
      )}

      {templates.length > 0 ? (
        <div className="flex flex-col gap-6 my-4 ml-4">
          {templates.map((template) => (
            <TemplateItem
              key={template.id}
              template={template}
              userRole={userRole}
              onCreateReport={createReport}
            />
          ))}
        </div>
      ) : (
        <p className="text-l mt-4">Шаблоны отсутствуют</p>
      )}

      <Modal isOpen={isModalOpen} onClose={closeModal}>
        <form onSubmit={handleUploadTemplate}>
          <h3 className="text-xl font-bold text-center mb-3">
            Шаблон для импорта
          </h3>
          <p className="text-l text-center mb-8">
            Поддерживаемые форматы: docx
          </p>

          <input
            type="file"
            name="template"
            accept=".docx"
            onChange={handleFileChange}
            className="mb-8 block"
            data-testid="template"
          />

          {uploadError && (
            <p className="text-center mb-3 bg-gradient-to-r from-transparent via-red-400/50 to-transparent">
              {uploadError}
            </p>
          )}

          <Button
            text={isUploading ? "Загружаю..." : "Загрузить"}
            disable={!selectedFile || isUploading}
            classes="block ml-auto disabled:border-zinc-500 disabled:text-zinc-500"
            type="submit"
          />
        </form>
      </Modal>
    </div>
  );
};

export default Templates;
