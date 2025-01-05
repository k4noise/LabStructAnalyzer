import { Link, useLoaderData, useNavigate } from "react-router";
import Modal from "../../components/Modal/Modal";
import { useState } from "react";
import { api, extractMessage } from "../../utils/sendRequest";
import Button from "../../components/Button/Button";
import { AllTemplatesInfo } from "../../model/template";

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
      <h2 className="text-3xl font-medium text-center mb-10">
        {courseName && `Отчеты лабораторных работ курса ${courseName}`}
      </h2>
      {data.teacher_interface && (
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
        <p className="font-bold">Доступные шаблоны:</p>
        {data.templates.length ? (
          <div className="flex flex-col gap-4 my-4 ml-4">
            {data.templates.map((templateProperties) => (
              <Link
                to={`/template/${templateProperties.template_id}`}
                key={templateProperties.template_id}
                className="underline"
              >
                {templateProperties.name}
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-l mt-4">Шаблоны отсутствуют</p>
        )}
      </div>
      <Modal isOpen={isOpen} onClose={handleClose}>
        <form onSubmit={handleUploadTemplate}>
          <h3 className="text-xl font-medium text-center mb-3">
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
