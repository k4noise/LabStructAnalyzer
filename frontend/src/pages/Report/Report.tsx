import React, { useCallback, useEffect, useState } from "react";
import { useLoaderData, useNavigate } from "react-router";
import BackButtonComponent from "../../components/BackButtonComponent";
import Modal from "../../components/Modal/Modal";
import { api, extractMessage } from "../../utils/sendRequest";
import Button from "../../components/Button/Button";
import { ReportInfoDto } from "../../model/reports";
import TemplateElements from "../../components/Template/TemplateElements";
import { Helmet } from "react-helmet";

/**
 * Условия фильтрации для различных режимов отображения.
 */
const displayModeFilterConditions = {
  prefer: (element: any) =>
    element.properties.displayMode === "prefer" ||
    element.properties.displayMode === "always",
  always: (element: any) => element.properties.displayMode === "always",
};

/**
 * Основной компонент отчета, отображающий различные элементы.
 */
const Report: React.FC = () => {
  const navigate = useNavigate();

  /**
   * Предварительно загруженные данные отчета
   */
  const { data: report } = useLoaderData<{ data: ReportInfoDto }>();

  const template = report.template;
  const [displayModeFilter, setDisplayModeFilter] = useState<string>("all");

  /**
   * Отфильтрованные элементы шаблона
   */
  const filteredElements = template?.elements.filter((element) => {
    if (!report.can_grade) {
      return true;
    }

    const condition = displayModeFilterConditions[displayModeFilter];
    return condition ? condition(element) : true;
  });

  const [error, setError] = useState<string | null>(null);

  const handleError = (error: any) => {
    setError(extractMessage(error.response) || error.message);
    setIsOpen(true);
  };

  const answers = report.embedded.answers.reduce((acc, answer) => {
    acc[answer.id] = {
      ...answer,
      given_score: answer.score,
    };
    return acc;
  }, {} as Record<string, any>);

  const [updatedAnswers, setUpdatedAnswers] =
    useState<Record<string, any>>(answers);

  const updateAnswers = (answer: any) => {
    setUpdatedAnswers((prevItems) => ({
      ...prevItems,
      [answer.id]: {
        ...prevItems[answer.id],
        ...answer,
      },
    }));
  };

  /**
   * Состояние модального окна редактирования свойств ответа (открыто/закрыто)
   */
  const [isOpen, setIsOpen] = useState(false);

  const handleClose = () => {
    setIsOpen(false);
    setError(null);
  };

  const [buttonState, setButtonState] = useState<Record<string, boolean>>({});

  const saveReportAnswers = useCallback(async () => {
    try {
      await api.patch(
        `/api/v1/reports/${report.id}`,
        Object.values(updatedAnswers)
      );
    } catch (error) {
      handleError(error);
    }
  }, [report.id, updatedAnswers]);

  useEffect(() => {
    if (report.status === "created" || report.status === "saved") {
      const intervalId = setInterval(async () => {
        await saveReportAnswers();
      }, 300000); // каждые 5 минут

      return () => clearInterval(intervalId);
    }
  }, [report.id, report.status, saveReportAnswers]);

  const handleActions = async (event: React.BaseSyntheticEvent) => {
    event.preventDefault();
    const nativeEvent = event?.nativeEvent as SubmitEvent | undefined;
    const buttonName = (nativeEvent?.submitter as HTMLButtonElement)?.name;
    const isSendReport = buttonName === "send";
    const isSaveReport = buttonName === "save";
    const isGradeReport = buttonName === "grade";
    const isEditReport = buttonName === "edit";

    try {
      setButtonState({ [buttonName]: true });

      if (isGradeReport) {
        await api.patch(
          `/api/v1/reports/${report.id}/grade`,
          Object.values(updatedAnswers)
        );
        navigate(`/template/${template.id}/reports`);
      } else if (isSaveReport) {
        await saveReportAnswers();
      } else if (isSendReport) {
        await saveReportAnswers();
        if (report.status === "created" || report.status === "saved") {
          await api.post(`/api/v1/reports/${report.id}/submit`);
        } else if (report.status === "submitted") {
          await api.delete(`/api/v1/reports/${report.id}/submit`);
        }
        navigate("/templates");
      } else if (isEditReport) {
        const response = await api.post(
          `/api/v1/templates/${template.id}/reports`
        );
        navigate(`/report/${response.data.id}`);
      }
      setButtonState({ [buttonName]: false });
    } catch (error) {
      handleError(error);
    }
  };

  return (
    <>
      <Helmet>
        <title>{`Отчет ${template.name}`}</title>
      </Helmet>
      <form onSubmit={(e) => handleActions(e)}>
        <BackButtonComponent positionClasses="" />
        <h1 className="inline-block text-3xl font-bold text-center mt-12 mb-10 w-full bg-transparent">
          {template.name}
        </h1>

        {report.grader_name && (
          <p className="mb-4">{`Проверил: ${report.grader_name}`}</p>
        )}

        {report.score ? (
          <p className="mb-4">
            {`Количество баллов: ${report.score}/${template.maxScore}`}
          </p>
        ) : (
          <p className="mb-4">
            {`Максимальное количество баллов: ${template.maxScore}`}
          </p>
        )}

        {report.can_grade &&
          (report.status === "submitted" || report.status === "graded") && (
            <div className="flex gap-3 items-center mb-3">
              Режим просмотра:
              <Button
                text="Полный"
                onClick={() => setDisplayModeFilter("all")}
                classes={`${
                  displayModeFilter === "all" ? "bg-blue-500/50" : ""
                }`}
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
            answers: updatedAnswers,
            updateAnswer: updateAnswers,
            editable: report.status === "created" || report.status === "saved",
            graderView:
              report.status === "submitted" || report.status === "graded",
            hintLink: report.links?.get_hint.href,
          }}
        />

        <div className="flex justify-end gap-5 mt-10">
          <Button
            text="Закрыть"
            onClick={() =>
              navigate(
                report.can_grade
                  ? `/template/${template.id}/reports`
                  : "/templates"
              )
            }
          />

          {(report.status === "created" || report.status === "saved") &&
            !report.can_grade && (
              <>
                <Button
                  text={buttonState?.save ? "Сохраняю..." : "Сохранить"}
                  type="submit"
                  name="save"
                  disabled={buttonState?.save}
                />
                <Button
                  text={
                    buttonState?.send
                      ? report.status === "submitted"
                        ? "Отменяю отправку..."
                        : "Отправляю на проверку..."
                      : report.status === "submitted"
                      ? "Отменить отправку"
                      : "Отправить на проверку"
                  }
                  type="submit"
                  name="send"
                  disabled={buttonState?.send}
                />
              </>
            )}

          {report.status === "graded" && !report.can_grade && (
            <Button
              text={
                buttonState?.edit
                  ? "Перехожу к редактированию..."
                  : "Редактировать"
              }
              type="submit"
              name="edit"
              disabled={buttonState?.edit}
            />
          )}

          {(report.status === "submitted" || report.status === "graded") &&
            report.can_grade && (
              <Button
                text={buttonState?.grade ? "Сохраняю оценки..." : "Оценить"}
                type="submit"
                name="grade"
                disabled={buttonState?.grade}
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
    </>
  );
};

export default Report;
