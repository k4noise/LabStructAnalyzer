import React, { useState, useCallback } from "react";
import { useLoaderData, useNavigate } from "react-router";
import { FieldValues, useForm } from "react-hook-form";
import {
  TemplateElementModel,
  AnswerElement,
} from "../../model/templateElement";
import BackButtonComponent from "../../components/BackButtonComponent";
import Modal from "../../components/Modal/Modal";
import { api, extractMessage } from "../../utils/sendRequest";
import Button from "../../components/Button/Button";
import TemplateElements from "../../components/Template/TemplateElements";
import EditAnswer from "../../components/EditAnswer/EditAnswer";
import DraggablePopover from "../../components/DraggablePopover/DraggablePopover";
import { Helmet } from "react-helmet";
import WeightToScoreManager from "../../manager/WeightToScoreManager";
import { TemplateDetailResponse } from "../../model/template";

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
  const template = useLoaderData<TemplateDetailResponse>().data;
  const weightToScoreManager = new WeightToScoreManager([], template.max_score);

  /**
   * Отфильтрованные элементы шаблона
   */
  const filteredElements = template.embedded.elements.filter((element) => {
    const condition = displayModeFilterConditions[displayModeFilter];
    return condition ? condition(element) : true;
  });

  const [error, setError] = useState<string | null>(null);

  const handleError = (error: any) => {
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

  const [editButtonClientRect, setEditButtonClientRect] =
    useState<DOMRect | null>(null);

  const [updatedElements, setUpdatedElements] = useState<{
    [id: string]: Partial<TemplateElementModel>;
  }>({});

  /**
   * Обновляет элементы шаблона с использованием функционального обновления состояния.
   */
  const updateElements = useCallback(
    (id: string, updatedProperties: Partial<AnswerElement["properties"]>) => {
      setIsOpen(false);
      weightToScoreManager.changeWeightsSum(
        selectedElement.properties.weight - updatedProperties.weight
      );
      setUpdatedElements((prevItems) => ({
        ...prevItems,
        [id]: {
          ...prevItems[id],
          element_id: id,
          properties: { ...prevItems[id]?.properties, ...updatedProperties },
        },
      }));
      selectedElement.properties.weight = updatedProperties.weight;
      selectedElement.properties.editNow = false;
      setSelectedElement(null);
    },
    [selectedElement, weightToScoreManager]
  );

  const { register, handleSubmit } = useForm();

  /**
   * Состояние модального окна редактирования свойств ответа (открыто/закрыто)
   * @type {boolean}
   */
  const [isOpen, setIsOpen] = useState(false);

  /**
   * Закрывает модальное окно
   * @function
   */
  const handleClose = () => {
    setIsOpen(false);
    setError(null);
  };

  const handleSelectAnswer = useCallback(
    (event: React.MouseEvent, element: AnswerElement) => {
      if (selectedElement) {
        selectedElement.properties.editNow = false;
      }
      const updatedElement = updatedElements[element.element_id];
      const elementForEdit: AnswerElement =
        (updatedElement as AnswerElement) ?? element;
      elementForEdit.properties.editNow = true;

      setSelectedElement(elementForEdit);
      setEditButtonClientRect(
        (event.target as HTMLElement).getBoundingClientRect()
      );
    },
    [selectedElement, updatedElements]
  );

  const [buttonState, setButtonState] = useState<{
    [buttonName: string]: boolean;
  }>({});

  const handleReset = () => {
    if (selectedElement) selectedElement.properties.editNow = false;
    weightToScoreManager.reset();
    setSelectedElement(null);
    setUpdatedElements({});
  };

  const handleSaveTemplate = async (
    data: FieldValues,
    event?: React.BaseSyntheticEvent
  ) => {
    const nativeEvent = event?.nativeEvent as SubmitEvent | undefined;
    const buttonName = (nativeEvent?.submitter as HTMLButtonElement)?.name;
    const isPublishTemplate = buttonName === "publish";

    const templateWithUpdatedData = {
      max_score: Number(data.maxScore) || 0,
    };

    try {
      setButtonState(isPublishTemplate ? { publish: true } : { update: true });

      const linkHref = isPublishTemplate
        ? template.links.publish?.href
        : template.links.update?.href;

      if (!linkHref) {
        throw new Error("Нет прав для выполнения действия");
      }

      isPublishTemplate
        ? await api.post(linkHref, templateWithUpdatedData)
        : await api.patch(linkHref, templateWithUpdatedData);

      setButtonState(
        isPublishTemplate ? { publish: false } : { update: false }
      );

      if (isPublishTemplate) {
        navigate("/templates");
      }
    } catch (error) {
      setButtonState({});
      handleError(error);
    }
  };

  const handleDelete = async () => {
    if (!template.links.delete) {
      handleError(new Error("Нет прав для удаления шаблона"));
      return;
    }

    try {
      setButtonState({ delete: true });
      await api.delete(template.links.delete.href);
      setButtonState({ delete: false });
      navigate("/templates");
    } catch (error) {
      setButtonState({});
      handleError(error);
    }
  };

  const canEdit = !!template.links.update;
  const canPublish = !!template.links.publish;
  const canDelete = !!template.links.delete;

  return (
    <>
      <Helmet>
        <title>
          {(template.isDraft ? "Черновик " : "Шаблон ") + template.name}
        </title>
      </Helmet>
      <form onReset={handleReset} onSubmit={handleSubmit(handleSaveTemplate)}>
        <BackButtonComponent positionClasses="" />
        {canEdit && template.isDraft ? (
          <input
            className="text-3xl font-bold text-center mt-12 mb-10 w-full
        bg-transparent border-b border-zinc-200 dark:border-zinc-950
        focus:outline-none focus:border-zinc-950 dark:focus:border-zinc-200"
            defaultValue={template.name}
            {...register("name")}
          />
        ) : (
          <h1 className="inline-block text-3xl font-bold text-center mt-12 mb-10 w-full bg-transparent">
            {template.name}
          </h1>
        )}
        <p className="opacity-60 mb-4">
          Максимальное количество баллов:
          {canEdit && template.isDraft ? (
            <input
              type="number"
              min="0"
              defaultValue={template.maxScore}
              className="w-20 ml-3 bg-transparent border-b focus:outline-none border-zinc-950 dark:border-zinc-200"
              {...register("maxScore")}
            />
          ) : (
            ` ${template.max_score}`
          )}
        </p>
        {canEdit && (
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
        <TemplateElements
          elements={filteredElements}
          answerContextProps={{
            handleSelectAnswerForEdit: handleSelectAnswer,
            editAnswerPropsMode: canEdit,
            weightToScoreManager: weightToScoreManager,
          }}
        />
        <div className="flex justify-end gap-5 mt-10">
          {canEdit ? (
            <>
              {canDelete && (
                <Button
                  text={buttonState?.delete ? "Удаляю..." : "Удалить"}
                  onClick={handleDelete}
                  disable={buttonState?.delete}
                  classes="disabled:border-zinc-500 disabled:text-zinc-500"
                />
              )}
              <Button text="Сброс" type="reset" />
            </>
          ) : (
            <Button text="Закрыть" onClick={() => navigate("/templates")} />
          )}
          {canEdit && (
            <Button
              text={buttonState?.update ? "Сохраняю..." : "Сохранить"}
              type="submit"
              name="update"
              disable={buttonState?.update}
              classes="disabled:border-zinc-500 disabled:text-zinc-500"
            />
          )}
          {canPublish && (
            <Button
              text={buttonState?.publish ? "Публикую..." : "Опубликовать"}
              type="submit"
              name="publish"
              disable={buttonState?.publish}
              classes="disabled:border-zinc-500 disabled:text-zinc-500"
            />
          )}
        </div>
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
        </div>
      </Modal>
      <DraggablePopover
        isOpen={!!selectedElement}
        onClose={() => {
          if (selectedElement) {
            selectedElement.properties.editNow = false;
          }
          setSelectedElement(null);
        }}
        anchorElementRect={editButtonClientRect}
      >
        <EditAnswer element={selectedElement} onSave={updateElements} />
      </DraggablePopover>
    </>
  );
};

export default Template;
