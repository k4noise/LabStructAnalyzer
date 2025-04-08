import React, { useCallback, useEffect, useState } from "react";
import { useLoaderData, useNavigate } from "react-router";
import { TemplateModel } from "../../model/template";
import { TemplateElementModel } from "../../model/templateElement";
import BackButtonComponent from "../../components/BackButtonComponent";
import Modal from "../../components/Modal/Modal";
import { api, extractMessage } from "../../utils/sendRequest";
import Button from "../../components/Button/Button";
import { AnswerModel } from "../../model/answer";
import { ReportInfoDto } from "../../model/reports";
import TemplateElements from "../../components/Template/TemplateElements";
import { Helmet } from "react-helmet";

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
const Report: React.FC = () => {
  const navigate = useNavigate();
  /**
   * Предварительно загруженные данные шаблона и отчета
   */
  const { template, report } = useLoaderData<{
    template: TemplateModel;
    report: ReportInfoDto;
  }>();

  const [displayModeFilter, setDisplayModeFilter] = useState<string>(
    report.status === "graded" ? "all" : "always"
  );

  /**
   * Отфильтрованные элементы шаблона
   */
  const filteredElements = template?.elements.filter((element) => {
    const condition = displayModeFilterConditions[displayModeFilter];
    return condition ? condition(element) : true;
  });

  const [error, setError] = useState<string>(null);

  const handleError = (error) => {
    setError(extractMessage(error.response) || error.message);
    setIsOpen(true);
  };

  const answers = {};
  if (report?.current_answers) {
    for (const answer of report.current_answers) {
      answers[answer.element_id] = {
        ...answer,
        given_score: answer.score,
      };
      if (report.can_grade && report.status != "graded") {
        // оценка пустых ответов как неправильных
        if (answer.data == null) {
          answers[answer.element_id].score = 0;
        }
        // значение по умолчанию для позитивного оценивания
        else if (answers[answer.element_id].score == null)
          answers[answer.element_id].score = 1;
      }
    }
  }

  const [updatedAnswers, setUpdatedAnswers] = useState<{
    [id: string]: AnswerModel;
  }>(answers);

  const updateAnswers = (answer: AnswerModel) => {
    setUpdatedAnswers((prevItems) => ({
      ...prevItems,
      [answer.element_id]: {
        ...prevItems[answer.element_id],
        ...answer,
      },
    }));
  };

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
    setUpdatedAnswers({});
  };

  const [buttonState, setButtonState] = useState<{
    [buttonName: string]: boolean;
  }>({});

  const saveReportAnswers = useCallback(async () => {
    try {
      await api.patch(
        `/api/v1/reports/${report.report_id}`,
        Object.values(updatedAnswers)
      );
    } catch (error) {
      handleError(error);
    }
  }, [report.report_id, updatedAnswers]);

  useEffect(() => {
    if (!report.can_grade) {
      const intervalId = setInterval(async () => {
        await saveReportAnswers();
      }, 300000); // каждые 5 минут

      return () => clearInterval(intervalId);
    }
  }, [report.report_id, report.can_grade, saveReportAnswers]);

  const handleSaveReport = async (event: React.BaseSyntheticEvent) => {
    event.preventDefault();
    const nativeEvent = event?.nativeEvent as SubmitEvent | undefined;
    const buttonName = (nativeEvent?.submitter as HTMLButtonElement)?.name;
    const isSendTemplate = buttonName === "send";
    const isGradeTemplate = buttonName === "grade";

    try {
      setButtonState({ [buttonName]: true });
      if (isGradeTemplate) {
        await api.patch(
          `/api/v1/reports/${report.report_id}/grade`,
          Object.values(updatedAnswers)
        );
        navigate(`/template/${template.template_id}/reports`);
      } else {
        await saveReportAnswers();
        if (isSendTemplate) {
          report.can_edit
            ? await api.post(`/api/v1/reports/${report.report_id}/submit`)
            : await api.delete(`/api/v1/reports/${report.report_id}/submit`);
        }
        navigate("/templates");
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
      <form onSubmit={(e) => handleSaveReport(e)}>
        <BackButtonComponent positionClasses="" />
        <h1 className="inline-block text-3xl font-bold text-center mt-12 mb-10 w-full bg-transparent">
          {template.name}
        </h1>
        {report.can_grade ? (
          <p className="mb-4">{`Выполнил: ${report.author_name}`}</p>
        ) : (
          <>
            {report.grader_name && (
              <p className="mb-4">{`Проверил: ${report.grader_name}`}</p>
            )}
            {report.score ? (
              <p className="mb-4">
                {`Количество баллов: ${report.score}/${template.max_score}`}
              </p>
            ) : (
              <p className="mb-4">
                {`Максимальное количество баллов: ${template.max_score}`}
              </p>
            )}
          </>
        )}
        {template.can_edit && (
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
            answers: updatedAnswers,
            updateAnswer: updateAnswers,
            editable:
              report.can_edit &&
              (report.status === "new" || report.status == "saved"),
            graderView: report.can_grade,
          }}
        />
        <div className="flex justify-end gap-5 mt-10">
          <Button
            text="Закрыть"
            onClick={() =>
              navigate(`/template/${template.template_id}/reports`)
            }
          />
          {report.can_edit && (
            <>
              <Button
                text={buttonState?.save ? "Сохраняю..." : "Сохранить"}
                type="submit"
                name="save"
                disable={buttonState?.save}
              />
              <Button
                text={
                  buttonState?.send
                    ? "Отправляю на проверку..."
                    : "Отправить на проверку"
                }
                type="submit"
                name="send"
                disable={buttonState?.send}
              />
            </>
          )}
          {!report.can_grade && !report.can_edit && (
            <Button
              text={
                buttonState?.send ? "Отменяю отправку..." : "Отменить отправку"
              }
              type="submit"
              name="send"
              disable={buttonState?.send}
            />
          )}
          {report.can_grade && (
            <Button
              text={buttonState?.grade ? "Сохраняю оценки..." : "Оценить"}
              type="submit"
              name="grade"
              disable={buttonState?.grade}
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
