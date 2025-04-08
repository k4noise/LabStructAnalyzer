import { useContext, useState } from "react";
import { AnswerElement } from "../../model/templateElement";
import AnswerContext from "../../context/AnswerContext";
import Button from "../Button/Button";
import Textarea from "../Textarea/TextareaComponent";
/**
 * Свойства для компонента ImageComponent.
 *
 * @interface ImageComponentProps
 * @property {ImageElement} element - Элемент изображения.
 */
interface AnswerComponentProps {
  element: AnswerElement;
}

/**
 * Компонент для отображения настройки ответа.
 */
const AnswerComponent: React.FC<AnswerComponentProps> = ({ element }) => {
  const [isRight, setIsRight] = useState<boolean | null>(null);
  const {
    handleSelectAnswerForEdit,
    editAnswerPropsMode,
    answers,
    weightToScoreManager,
    updateAnswer,
    editable,
    graderView,
  } = useContext(AnswerContext);
  const score = answers ? answers[element.element_id]?.score : 0;
  const onChangeAnswer = (e) =>
    updateAnswer({
      element_id: element.element_id,
      data: { text: e.target.value },
    });

  const changeScore = (score: number) => {
    setIsRight(score != 0);
    updateAnswer({
      element_id: element.element_id,
      score,
    });
  };
  return editAnswerPropsMode ? (
    <>
      <Button
        text="⚙️ Настройка ответа"
        classes={`mb-2 ${
          element.properties.editNow
            ? "!border-blue-500 dark:!text-blue-300 text-blue-600"
            : ""
        }`}
        onClick={(event) => {
          handleSelectAnswerForEdit(event, element);
        }}
      />
      <br />
      {(element.properties.customId ? `#${element.properties.customId} ` : "") +
        `(вес: ${
          element.properties.weight
        }, итого: ${weightToScoreManager.calcFinalScore(
          element.properties.weight
        )})`}
      <br />
    </>
  ) : (
    <>
      {element.properties.simple ? (
        <input
          type="text"
          className={`inline-block bg-transparent border-b w-full max-w-sm ${
            isRight
              ? "border-green-500 bg-green-500 bg-opacity-25 dark:bg-green-800 dark:bg-opacity-40"
              : isRight == false
              ? "border-red-500 bg-red-500 bg-opacity-25 dark:bg-red-800 dark:bg-opacity-40"
              : "border-zinc-950 dark:border-zinc-200"
          }`}
          placeholder="Ваш ответ"
          value={answers[element.element_id]?.data?.text ?? ""}
          onChange={onChangeAnswer}
          disabled={!editable}
        />
      ) : (
        <Textarea
          className={`block bg-transparent border rounded-xl w-full mt-4 p-4 overflow-hidden ${
            isRight
              ? "border-green-500"
              : isRight == false
              ? "border-red-500 bg-red-500 bg-opacity-25"
              : "border-zinc-950 dark:border-zinc-200"
          }`}
          placeholder="Ваш ответ"
          minRowsCount={5}
          onChange={onChangeAnswer}
          value={answers[element.element_id]?.data?.text ?? ""}
          disabled={!editable}
        />
      )}
      {editable && element.properties.data && (
        <span>{`Подсказка: ${element.properties.data}`}</span>
      )}
      {editable && (
        <span className="opacity-60">
          {" "}
          {`(max: ${element.properties.weight})`}
        </span>
      )}
      {!editable &&
        answers &&
        answers[element.element_id]?.given_score != null && (
          <span>
            {`${score > 0 ? "✔️" : "❌"}${score * element.properties.weight}/${
              element.properties.weight
            }`}
          </span>
        )}
      {graderView && (
        <>
          {answers[element.element_id]?.given_score != null && (
            <span className="mr-2">
              <br></br>Новая оценка:
            </span>
          )}
          <button
            type="button"
            className="text-3xl opacity-80"
            onClick={() => changeScore(1)}
          >
            ✔️
          </button>
          <button
            type="button"
            className="text-3xl opacity-80"
            onClick={() => changeScore(0)}
          >
            ❌
          </button>
        </>
      )}
    </>
  );
};

export default AnswerComponent;
