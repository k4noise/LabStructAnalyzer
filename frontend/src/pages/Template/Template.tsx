import React, { useState, useCallback, useMemo } from "react";
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

const displayModeFilterConditions = {
  prefer: (element: TemplateElementModel) =>
    element.properties.displayMode === "prefer" ||
    element.properties.displayMode === "always",
  always: (element: TemplateElementModel) =>
    element.properties.displayMode === "always",
};

interface TemplateUpdateRequest {
  name?: string;
  max_score?: number;
  elements?: Array<{
    action: "update";
    id: string;
    properties: Partial<AnswerElement["properties"]>;
  }>;
}

const Template: React.FC = () => {
  const navigate = useNavigate();
  const [displayModeFilter, setDisplayModeFilter] = useState<string>("all");

  const loaderData = useLoaderData() as { data: TemplateDetailResponse };
  const template = loaderData.data;

  const weightToScoreManager = useMemo(
    () =>
      new WeightToScoreManager(template.embedded.elements, template.max_score),
    [template.max_score]
  );

  const filteredElements = useMemo(
    () =>
      template.embedded.elements.filter((element) => {
        const condition =
          displayModeFilterConditions[
            displayModeFilter as keyof typeof displayModeFilterConditions
          ];
        return condition ? condition(element) : true;
      }),
    [template.embedded.elements, displayModeFilter]
  );

  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedElement, setSelectedElement] = useState<AnswerElement | null>(
    null
  );
  const [editButtonClientRect, setEditButtonClientRect] =
    useState<DOMRect | null>(null);

  const answersCache = useMemo(() => {
    const cache: { [id: string]: AnswerElement } = {};
    template.embedded.elements.forEach((el) => {
      if (el.type === "answer") {
        cache[el.id] = el;
      }
    });
    return cache;
  }, [template.embedded.elements]);

  const [updatedElements, setUpdatedElements] = useState<{
    [id: string]: Partial<AnswerElement["properties"]>;
  }>({});

  /**
   * Получает актуальный элемент с учетом локальных обновлений
   */
  const getCurrentElement = useCallback(
    (elementId: string): AnswerElement | null => {
      const original = answersCache[elementId];
      if (!original) return null;

      const updates = updatedElements[elementId];
      if (!updates) return original;

      return {
        ...original,
        properties: {
          ...original.properties,
          ...updates,
        },
      };
    },
    [answersCache, updatedElements]
  );

  const handleSelectAnswer = useCallback(
    (event: React.MouseEvent, element: AnswerElement) => {
      const currentElement = getCurrentElement(element.id) || element;

      const elementForEdit: AnswerElement = {
        ...currentElement,
        properties: {
          ...currentElement.properties,
          editNow: true,
        },
      };

      setSelectedElement(elementForEdit);
      setEditButtonClientRect(
        (event.target as HTMLElement).getBoundingClientRect()
      );
    },
    [getCurrentElement]
  );

  const updateElements = useCallback(
    (id: string, updatedProperties: Partial<AnswerElement["properties"]>) => {
      const oldElement = getCurrentElement(id);
      const oldWeight = oldElement?.properties.weight || 0;
      const newWeight = updatedProperties.weight || 0;

      weightToScoreManager.changeWeightsSum(newWeight - oldWeight);

      setUpdatedElements((prev) => ({
        ...prev,
        [id]: {
          ...prev[id],
          ...updatedProperties,
          editNow: false,
        },
      }));

      setSelectedElement(null);
    },
    [getCurrentElement, weightToScoreManager]
  );

  const { register, handleSubmit } = useForm();

  const handleClose = () => {
    setIsOpen(false);
    setError(null);
  };

  const handleError = (error: any) => {
    setError(extractMessage(error.response) || error.message);
    setIsOpen(true);
  };

  const [buttonState, setButtonState] = useState<{
    [buttonName: string]: boolean;
  }>({});

  const handleReset = () => {
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

    const templateWithUpdatedData: TemplateUpdateRequest = {
      max_score: Number(data.maxScore) || 0,
    };

    const changedElements = Object.entries(updatedElements)
      .filter(([_, props]) => Object.keys(props).length > 0)
      .map(([id, properties]) => ({
        action: "update",
        id,
        properties,
      }));

    if (changedElements.length > 0) {
      templateWithUpdatedData.elements = changedElements;
    }

    try {
      setButtonState(isPublishTemplate ? { publish: true } : { update: true });

      const linkHref = isPublishTemplate
        ? template.links.publish?.href
        : template.links.update?.href;

      if (!linkHref) {
        throw new Error("Нет прав для выполнения действия");
      }

      if (isPublishTemplate) {
        await api.post(linkHref, templateWithUpdatedData);
      } else {
        await api.patch(linkHref, templateWithUpdatedData);
      }

      setButtonState(
        isPublishTemplate ? { publish: false } : { update: false }
      );

      if (isPublishTemplate) {
        navigate("/templates");
      } else {
        setUpdatedElements({});
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

  const answerContextProps = {
    handleSelectAnswerForEdit: handleSelectAnswer,
    editAnswerPropsMode: canEdit,
    weightToScoreManager,
    getCurrentElement,
    updatedElements,
  };

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
            className="text-3xl font-bold text-center mt-12 mb-10 w-full bg-transparent border-b border-zinc-200 dark:border-zinc-950 focus:outline-none focus:border-zinc-950 dark:focus:border-zinc-200"
            defaultValue={template.name}
            {...register("name")}
          />
        ) : (
          <h1 className="text-3xl font-bold text-center mt-12 mb-10 w-full bg-transparent">
            {template.name}
          </h1>
        )}
        <p className="opacity-60 mb-4">
          Максимальное количество баллов:
          {canEdit && template.isDraft ? (
            <input
              type="number"
              min="0"
              defaultValue={template.max_score}
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
          answerContextProps={answerContextProps}
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
        onClose={() => setSelectedElement(null)}
        anchorElementRect={editButtonClientRect}
      >
        {selectedElement && (
          <EditAnswer element={selectedElement} onSave={updateElements} />
        )}
      </DraggablePopover>
    </>
  );
};

export default Template;
