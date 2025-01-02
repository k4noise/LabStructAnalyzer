import React, { useState } from "react";
import {
  TemplateModel,
  TemplateElementModel,
  AnswerElement,
} from "../../model/template";
import TextComponent from "../../components/Template/TextComponent";
import ImageComponent from "../../components/Template/ImageComponent";
import HeaderComponent from "../../components/Template/HeaderComponent";
import TableComponent from "../../components/Template/TableComponent";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import AnswerComponent from "../../components/Template/AnswerComponent";
import { useLoaderData } from "react-router";
import BackButtonComponent from "../../components/BackButtonComponent";
import QuestionAnswerComponent from "../../components/Template/QuestionAnswerComponent";
import Modal from "../../components/Modal/Modal";
import AnswerContext from "../../context/AnswerContext";
import EditAnswerModal from "../../components/EditAnswer/EditAnswer";

/**
 * Карта соответствий типов элементов и компонентов для рендеринга.
 *
 * @constant
 * @type {Record<string, React.FC<any>>}
 */
const componentMap: Record<
  string,
  React.FC<{ element: TemplateElementModel }>
> = {
  text: TextComponent,
  image: ImageComponent,
  header: HeaderComponent,
  question: QuestionAnswerComponent,
  table: TableComponent,
  answer: AnswerComponent,
};

/**
 * Основной компонент шаблона, отображающий различные элементы.
 */
const Template: React.FC = () => {
  /**
   * Предварительно загруженные данные шаблона
   */
  const { data: template } = useLoaderData<{ data: TemplateModel }>();
  /**
   * Состояние выбранного элемента ответа для редактирования свойств
   * @type {AnswerElement | null}
   */
  const [selectedElement, setSelectedElement] = useState<AnswerElement | null>(
    null
  );

  const [updatedElements, setUpdatedElements] = useState({});
  const updateElements = (
    id: string,
    updatedProperties: Partial<AnswerElement["properties"]>
  ) => {
    setIsOpen(false);
    setUpdatedElements((prevItems) => ({
      ...prevItems,
      [id]: {
        ...prevItems[id],
        properties: { ...prevItems[id]?.properties, ...updatedProperties },
      },
    }));
  };

  /**
   * Состояние модального окна редактирования свойств ответа (открыто/закрыто)
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

  const handleSelectAnswer = (element: AnswerElement) => {
    const updatedElement = updatedElements[element.element_id];
    setSelectedElement(updatedElement ?? element);
    handleOpen();
  };

  const handleReset = () => {
    setSelectedElement(null);
    setUpdatedElements({});
  };

  return (
    <>
      <form onSubmit={(event) => event.preventDefault()} onReset={handleReset}>
        <BackButtonComponent positionClasses="" />
        <input
          className="text-3xl font-medium text-center mt-12 mb-10 w-full
        bg-transparent border-b border-zinc-200 dark:border-zinc-950
        focus-visible:outline-none focus-visible:border-zinc-950 dark:focus-visible:border-zinc-200"
          defaultValue={template.name}
        />
        <p className="opacity-60">
          Максимальное количество баллов:
          <input
            type="number"
            min="0"
            defaultValue={template.max_score}
            className="w-20 mb-4 ml-3 bg-transparent border-b focus-visible:outline-none border-zinc-950 dark:border-zinc-200"
          />
        </p>
        <AnswerContext.Provider
          value={{ handleSelectAnswerForEdit: handleSelectAnswer }}
        >
          {template?.elements.map((element) => renderElement(element))}
        </AnswerContext.Provider>
        <div className="flex justify-end gap-6 mt-10">
          <button
            className="px-2 py-1 border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950"
            type="reset"
          >
            Сброс
          </button>
          <button className="px-2 py-1 border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950">
            Сохранить
          </button>
        </div>

        {/* Ни в коем случае не удаляйте этот элемент, так как не будут сгенерированы нужные классы отступов и размеров заголовков*/}
        <span className="ml-4 ml-8 ml-12 ml-16 ml-20 ml-24 ml-28 ml-32 ml-36 ml-40 text-3xl text-2xl"></span>
      </form>
      <Modal isOpen={isOpen} onClose={handleClose}>
        <EditAnswerModal element={selectedElement} onSave={updateElements} />
      </Modal>
    </>
  );
};

/**
 * Рендерит элемент шаблона на основе его типа.
 *
 * @param {TemplateElement} element - Элемент шаблона для рендеринга.
 */
const renderElement = (element: TemplateElementModel): React.ReactNode => {
  const Component = componentMap[element.element_type] || null;
  if (Component) {
    return <Component element={element} key={element.element_id} />;
  }

  if (Array.isArray(element.properties.data)) {
    return (
      <div
        className={`my-5 ${getMarginLeftStyle(
          element.properties.nestingLevel
        )}`}
        key={element.element_id}
      >
        {element.properties.data.map((childElement) =>
          renderElement(childElement)
        )}
      </div>
    );
  }

  return null;
};

export default Template;
export { renderElement };
