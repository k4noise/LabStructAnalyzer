import { useNavigate } from "react-router";
import Modal from "../../components/Modal/Modal";
import { useEffect, useState } from "react";
import { sendTemplate } from "../../actions/sendTemplate";
import { getCourseName } from "../../actions/getCourseName";

/**
 * Компонент для управления шаблонами курса
 *
 * @component
 * @returns {JSX.Element} Страница шаблонов с возможностью загрузки нового шаблона
 */
const Templates = () => {
  /**
   * Хук навигации для перемещения между страницами
   * @type {Function}
   */
  const navigate = useNavigate();

  /**
   * Состояние названия курса
   * @type {string|null}
   */
  const [courseName, setCourseName] = useState<string | null>(null);

  /**
   * Состояние модального окна (открыто/закрыто)
   * @type {boolean}
   */
  const [isOpen, setIsOpen] = useState(false);

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
   * Получить имя курса.
   * Выполняется только тогда, когда в текущем состоянии нет имени.
   * Если имени нет, то получает его и устанавливает
   * @function
   */
  const getName = async () => {
    if (courseName) {
      return;
    }

    const { data, error, description } = await getCourseName();

    if (error) {
      navigate(`/error?code=${error}&description=${description}`);
      return;
    }

    setCourseName(data.name);
  };

  useEffect(() => {
    getName();
  }, []);

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
    const { data, error, description } = await sendTemplate(formData);
    if (error) {
      navigate(`/error?code=${error}&description=${description}`);
    }
    if (data) {
      localStorage.setItem("pageData", JSON.stringify(data));
      navigate("/template");
    }
  };

  return (
    <div>
      <h2 className="text-3xl font-medium text-center mb-10">
        Отчеты лабораторных работ {courseName ? `курса ${courseName}` : ""}
      </h2>
      <button
        className="text-l p-4 rounded-xl underline mb-5"
        onClick={handleOpen}
      >
        + Добавить новый шаблон
      </button>
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
            className="mb-8"
            data-testid="template"
          />
          <button className="block px-2 py-1 ml-auto border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950">
            Загрузить
          </button>
        </form>
      </Modal>
      <p className="text-l">Нет шаблонов</p>
    </div>
  );
};

export default Templates;
