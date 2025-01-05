import React, { useState, memo, useMemo, useCallback } from "react";
import { useLoaderData, useNavigate } from "react-router";
import { FieldValues, useForm } from "react-hook-form";
import { TemplateModel, UpdateTemplateModel } from "../../model/template";
import {
  TemplateElementModel,
  AnswerElement,
} from "../../model/templateElement";
import TextComponent from "../../components/Template/TextComponent";
import ImageComponent from "../../components/Template/ImageComponent";
import HeaderComponent from "../../components/Template/HeaderComponent";
import TableComponent from "../../components/Template/TableComponent";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import AnswerComponent from "../../components/Template/AnswerComponent";
import BackButtonComponent from "../../components/BackButtonComponent";
import QuestionAnswerComponent from "../../components/Template/QuestionAnswerComponent";
import Modal from "../../components/Modal/Modal";
import AnswerContext from "../../context/AnswerContext";
import EditAnswerModal from "../../components/EditAnswer/EditAnswer";
import { api, extractMessage } from "../../utils/sendRequest";
import Button from "../../components/Button/Button";

const MemoizedTextComponent = memo(TextComponent);
const MemoizedImageComponent = memo(ImageComponent);
const MemoizedHeaderComponent = memo(HeaderComponent);
const MemoizedQuestionAnswerComponent = memo(QuestionAnswerComponent);
const MemoizedTableComponent = memo(TableComponent);
const MemoizedAnswerComponent = memo(AnswerComponent);

const renderElement = (element: TemplateElementModel): React.ReactNode => {
  const Component = componentMap[element.element_type] || null;

  const marginLeftStyle = getMarginLeftStyle(element.properties.nestingLevel);

  if (Component) {
    return <Component element={element} key={element.element_id} />;
  }

  if (Array.isArray(element.properties.data)) {
    return (
      <div className={`my-5 ${marginLeftStyle}`} key={element.element_id}>
        {element.properties.data.map(renderElement)}
      </div>
    );
  }

  return null;
};

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
  text: MemoizedTextComponent,
  image: MemoizedImageComponent,
  header: MemoizedHeaderComponent,
  question: MemoizedQuestionAnswerComponent,
  table: MemoizedTableComponent,
  answer: MemoizedAnswerComponent,
};

/**
 * Условия фильтрации для различных режимов отображения.
 */
const displayModeFilterConditions = {
  prefer: (element: TemplateElementModel) =>
    element.properties.displayMode === "prefer" ||
    element.properties.displayMode === "always",
  always: (element: TemplateElementModel) =>
    element.properties.displayMode === "always",
};

/**
 * Основной компонент шаблона, отображающий различные элементы.
 */
const Template: React.FC = () => {
  const navigate = useNavigate();

  const [displayModeFilter, setDisplayModeFilter] = useState<string>("all");

  /**
   * Предварительно загруженные данные шаблона
   */
  const { data: template } = useLoaderData<{ data: TemplateModel }>();

  /**
   * Отфильтрованные элементы шаблона с использованием useMemo.
   */
  const filteredElements = useMemo(() => {
    return template?.elements.filter((element) => {
      const condition = displayModeFilterConditions[displayModeFilter];
      return condition ? condition(element) : true;
    });
  }, [template?.elements, displayModeFilter]);

  const [error, setError] = useState<string>(null);

  const handleError = (error) => {
    setError(extractMessage(error.response) || error.message);
    setIsOpen(true);
  };

  /**
   * Состояние выбранного элемента ответа для редактирования свойств
   * @type {AnswerElement | null}
   */
  const [selectedElement, setSelectedElement] = useState<AnswerElement | null>(
    null
  );

  const [updatedElements, setUpdatedElements] = useState<{
    [id: string]: Partial<TemplateElementModel>;
  }>({});

  /**
   * Обновляет элементы шаблона с использованием функционального обновления состояния.
   */
  const updateElements = useCallback(
    (id: string, updatedProperties: Partial<AnswerElement["properties"]>) => {
      setIsOpen(false);
      setUpdatedElements((prevItems) => ({
        ...prevItems,
        [id]: {
          ...prevItems[id],
          element_id: id,
          properties: { ...prevItems[id]?.properties, ...updatedProperties },
        },
      }));
    },
    []
  );

  const { register, handleSubmit } = useForm();

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
    setError(null);
    setSelectedElement(null);
  };

  const handleSelectAnswer = useCallback(
    (element: AnswerElement) => {
      const updatedElement = updatedElements[element.element_id];
      setSelectedElement((updatedElement as AnswerElement) ?? element);
      handleOpen();
    },
    [updatedElements]
  );

  const [buttonState, setButtonState] = useState<{
    [buttonName: string]: boolean;
  }>({});

  const handleReset = () => {
    setSelectedElement(null);
    setUpdatedElements({});
  };

  const handleSaveTemplate = async (data: FieldValues) => {
    const templateWithUpdatedData: UpdateTemplateModel = {
      is_draft: false,
      name: data.name,
      max_score: data.max_score,
      updated_elements: Object.values(updatedElements),
    };
    try {
      setButtonState({ update: true });
      await api.patch(
        `/api/v1/templates/${template.template_id}`,
        templateWithUpdatedData
      );
      setButtonState({ update: false });
      navigate("/templates");
    } catch (error) {
      handleError(error);
    }
  };

  const handleDelete = async () => {
    try {
      setButtonState({ delete: true });
      await api.delete(`/api/v1/templates/${template.template_id}`);
      setButtonState({ delete: false });
      navigate("/templates");
    } catch (error) {
      handleError(error);
    }
  };

  /**
   * Рендерит элемент шаблона на основе его типа.
   * Использует useCallback для мемоизации функции.
   */
  const memoizedRenderElement = useCallback(renderElement, [componentMap]);

  return (
    <>
      <form onReset={handleReset} onSubmit={handleSubmit(handleSaveTemplate)}>
        <BackButtonComponent positionClasses="" />
        {template.teacher_interface && template.is_draft ? (
          <input
            className="text-3xl font-medium text-center mt-12 mb-10 w-full
        bg-transparent border-b border-zinc-200 dark:border-zinc-950
        focus:outline-none focus:border-zinc-950 dark:focus:border-zinc-200"
            defaultValue={template.name}
            {...register("name")}
          />
        ) : (
          <h1 className="inline-block text-3xl font-medium text-center mt-12 mb-10 w-full bg-transparent">
            {template.name}
          </h1>
        )}
        <p className="opacity-60 mb-4">
          Максимальное количество баллов:
          {template.teacher_interface && template.is_draft ? (
            <input
              type="number"
              min="0"
              defaultValue={template.max_score}
              className="w-20 ml-3 bg-transparent border-b focus:outline-none border-zinc-950 dark:border-zinc-200"
              {...register("max_score")}
            />
          ) : (
            ` ${template.max_score}`
          )}
        </p>
        {template.teacher_interface && (
          <div className="flex gap-3 items-center mb-3">
            Режим просмотра:
            <Button
              text="Полный"
              onClick={() => setDisplayModeFilter("all")}
              classes={`${displayModeFilter === "all" ? "bg-blue-500/50" : ""}`}
            />
            <Button
              text="Сокращенный"
              onClick={() => setDisplayModeFilter("prefer")}
              classes={`${
                displayModeFilter === "prefer" ? "bg-blue-500/50" : ""
              }`}
            />
            <Button
              text="Минимальный"
              onClick={() => setDisplayModeFilter("always")}
              classes={`${
                displayModeFilter === "always" ? "bg-blue-500/50" : ""
              }`}
            />
          </div>
        )}

        <AnswerContext.Provider
          value={{ handleSelectAnswerForEdit: handleSelectAnswer }}
        >
          {filteredElements?.map(memoizedRenderElement)}
        </AnswerContext.Provider>
        <div className="flex justify-end gap-5 mt-10">
          {template.teacher_interface ? (
            <>
              <Button
                text={buttonState?.delete ? "Удаляю..." : "Удалить"}
                onClick={handleDelete}
                disable={buttonState?.delete}
                classes="disabled:border-zinc-500 disabled:text-zinc-500"
              />
              <Button text="Сброс" type="reset" />
            </>
          ) : (
            <Button text="Закрыть" onClick={() => navigate("/templates")} />
          )}
          <Button
            text={buttonState?.update ? "Сохраняю..." : "Сохранить"}
            type="submit"
            disable={buttonState?.update}
            classes="disabled:border-zinc-500 disabled:text-zinc-500"
          />
        </div>

        {/* Ни в коем случае не удаляйте этот элемент, так как не будут сгенерированы нужные классы отступов и размеров заголовков*/}
        <span className="ml-4 ml-8 ml-12 ml-16 ml-20 ml-24 ml-28 ml-32 ml-36 ml-40 text-3xl text-2xl"></span>
      </form>
      <Modal isOpen={isOpen} onClose={handleClose}>
        <div className="w-80">
          {error && (
            <p>
              Произошла ошибка:
              <br />
              <br />
              {error}
            </p>
          )}
          {!error && selectedElement && (
            <EditAnswerModal
              element={selectedElement}
              onSave={updateElements}
            />
          )}
        </div>
      </Modal>
    </>
  );
};

export default Template;
export { renderElement };
