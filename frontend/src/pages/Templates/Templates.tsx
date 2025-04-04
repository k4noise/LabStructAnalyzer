import { Link, useLoaderData, useNavigate } from "react-router";
import Modal from "../../components/Modal/Modal";
import { useState } from "react";
import { api, extractMessage } from "../../utils/sendRequest";
import Button from "../../components/Button/Button";
import { AllTemplatesInfo } from "../../model/template";

const getStatusClass = (status: string | null): string => {
  switch (status) {
    case "Новый":
      return "border-blue-600 text-blue-600";
    case "Создан":
      return "border-indigo-600 text-indigo-600";
    case "Сохранен":
      return "border-cyan-600 text-cyan-600";
    case "Отправлен на проверку":
      return "border-yellow-600 text-yellow-600";
    case "Проверен":
      return "border-green-600 text-green-600";
    default:
      return "dark:border-zinc-200 border-zinc-950";
  }
};

/**
 * Компонент для управления шаблонами курса
 *
 * @component
 * @returns {JSX.Element} Страница шаблонов с возможностью загрузки нового шаблона
 */
const Templates = () => {
  const { data } = useLoaderData<{ data: AllTemplatesInfo }>();
  const courseName = data.course_name;
  /**
   * Хук навигации для перемещения между страницами
   * @type {Function}
   */
  const navigate = useNavigate();

  /**
   * Состояние модального окна (открыто/закрыто)
   * @type {boolean}
   */
  const [isOpen, setIsOpen] = useState(false);

  /**
   * Состояние загрузки нового шаблона (в процессе загрузки/не загружается)
   * @type {boolean}
   */
  const [isTemplateUpload, setIsTemplateUpload] = useState(false);

  /**
   * Состояние сообщения об ошибке при загрузке шаблона
   * @type {string | null}
   */
  const [errorInUpload, setErrorInUpload] = useState<string | null>(null);

  /**
   * Открывает модальное окно
   * @function
   */
  const handleOpen = () => {
    setIsOpen(true);
  };

  /**
   * Закрывает модальное окно
   * @function
   */
  const handleClose = () => {
    setIsOpen(false);
  };

  /**
   * Обработчик загрузки шаблона.
   * Перенаправляет на страницу ошибки, если произошла ошибка
   *
   * @async
   * @function
   * @param {Event} event - Событие отправки формы
   */
  const handleUploadTemplate = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const template = formData.get("template");
    if (template && template["name"] == "") return;
    try {
      setIsTemplateUpload(true);
      const { data } = await api.post("/api/v1/templates", formData);
      setIsTemplateUpload(false);
      setErrorInUpload(null);
      navigate(`/template/${data.template_id}`);
    } catch (error) {
      setErrorInUpload(extractMessage(error.response));
    }
  };

  return (
    <div className="mt-8">
      <h2 className="text-3xl font-bold text-center mb-10">
        {courseName && `Отчеты лабораторных работ курса ${courseName}`}
      </h2>
      {data.can_upload && (
        <Button
          text="+ Добавить новый шаблон"
          onClick={handleOpen}
          classes="mb-6"
        />
      )}
      {!!data?.drafts?.length && (
        <div>
          <p className="font-bold">Черновики шаблонов:</p>
          <div className="ml-4 flex flex-col gap-4 my-4">
            {data.drafts.map((templateProperties) => (
              <Link
                to={`/template/${templateProperties.template_id}`}
                key={templateProperties.template_id}
                className="underline"
              >
                {templateProperties.name}
              </Link>
            ))}
          </div>
        </div>
      )}
      <div>
        <p className="font-bold">
          {data.can_upload ? "Опубликованные" : "Доступные"} шаблоны:
        </p>
        {data.templates.length ? (
          <div className="flex flex-col gap-4 my-4 ml-4">
            {data.templates.map((templateProperties) => (
              <span key={`${templateProperties.template_id}-items`}>
                <Link
                  to={
                    data.can_upload
                      ? `/template/${templateProperties.template_id}`
                      : templateProperties.report_id
                      ? `/report/${templateProperties.report_id}`
                      : `/report/new/${templateProperties.template_id}`
                  }
                  key={templateProperties.template_id}
                  className="underline mr-4"
                >
                  {templateProperties.name}
                </Link>
                {data.can_grade ? (
                  <Link
                    to={`/template/${templateProperties.template_id}/reports`}
                    className="text-base border px-2 py-1 dark:border-zinc-200 border-zinc-950 border-solid rounded-xl border-2"
                  >
                    Заполненные отчеты
                  </Link>
                ) : (
                  <span
                    className={`text-base border px-2 py-1 border-solid rounded-xl border-2 select-none ${getStatusClass(
                      templateProperties.report_status ?? "Новый"
                    )}`}
                  >
                    {templateProperties.report_status ?? "Новый"}
                  </span>
                )}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-l mt-4">Шаблоны отсутствуют</p>
        )}
      </div>
      <Modal isOpen={isOpen} onClose={handleClose}>
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
            className="mb-8 block"
            data-testid="template"
          />
          {errorInUpload && (
            <p className="text-center mb-3 bg-gradient-to-r from-transparent via-red-400/50 to-transparent">
              {errorInUpload}
            </p>
          )}
          <Button
            text={isTemplateUpload ? "Загружаю..." : "Загрузить"}
            classes="block ml-auto disabled:border-zinc-500 disabled:text-zinc-500"
            type="submit"
          />
        </form>
      </Modal>
    </div>
  );
};

export default Templates;
