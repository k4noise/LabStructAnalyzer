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
    updateAnswer,
    editable,
    graderView,
  } = useContext(AnswerContext);
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
        classes="ml-2 mb-2"
        onClick={(event) => {
          handleSelectAnswerForEdit(event, element);
        }}
      />
      <br />
    </>
  ) : (
    <>
      {element.properties.simple ? (
        <input
          type="text"
          className={`inline-block bg-transparent ml-4 border-b  w-full max-w-sm ${
            isRight
              ? "border-green-500"
              : isRight == false
              ? "border-red-500"
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
              ? "border-red-500"
              : "border-zinc-950 dark:border-zinc-200"
          }`}
          placeholder="Ваш ответ"
          minRowsCount={5}
          onChange={onChangeAnswer}
          value={answers[element.element_id]?.data?.text ?? ""}
          disabled={!editable}
        />
      )}
      {graderView && (
        <>
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
      {!graderView && !editable && answers[element.element_id].score >= 0 && (
        <span>
          {`${answers[element.element_id].score > 0 ? "✔️" : "❌"}${
            answers[element.element_id].score * element.properties.weight
          }/${element.properties.weight}`}
        </span>
      )}
    </>
  );
};

export default AnswerComponent;
