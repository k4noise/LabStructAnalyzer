import { useContext, useState } from "react";
import { AnswerElement } from "../../model/templateElement";
import AnswerContext from "../../context/AnswerContext";
import Button from "../Button/Button";
import Textarea from "../Textarea/TextareaComponent";

interface AnswerComponentProps {
  element: AnswerElement;
  withQuestion?: boolean;
}

const AnswerComponent: React.FC<AnswerComponentProps> = ({
  element,
  withQuestion,
}) => {
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

  const score = answers ? answers[element.element_id]?.score : null;

  const onChangeAnswer = (e: any) =>
    updateAnswer({
      element_id: element.element_id,
      data: { text: e.target.value },
    });

  const changeScore = (score: number) => {
    setIsRight(score !== 0);
    updateAnswer({
      element_id: element.element_id,
      score,
    });
  };

  if (editAnswerPropsMode) {
    return (
      <span className="inline-block align-middle mx-2 not-italic">
        <Button
          text="⚙️ Настройка ответа"
          classes={`!py-1 !px-3 !text-base transition-colors ${
            element.properties.editNow ? "!border-blue-500 !text-blue-400" : ""
          }`}
          onClick={(event) => {
            handleSelectAnswerForEdit(event, element);
          }}
        />
        <span className="block text-[11px] opacity-40 leading-none mt-1.5 text-center font-medium">
          {(element.properties.customId
            ? `#${element.properties.customId} `
            : "") +
            `(вес: ${
              element.properties.weight
            }, итого: ${weightToScoreManager.calcFinalScore(
              element.properties.weight
            )})`}
        </span>
      </span>
    );
  }

  return (
    <span className="not-italic inline">
      {!graderView && element.properties.data && (
        <details className="inline-grid mr-4 align-middle">
          <summary className="text-base select-none cursor-pointer opacity-60 hover:opacity-100">
            [Подсказка]
          </summary>
          <span className="absolute mt-1 max-w-lg truncate bg-zinc-200 dark:bg-zinc-900 text-sm px-2 py-1 rounded shadow-lg z-10">
            {element.properties.data}
          </span>
        </details>
      )}

      {graderView &&
        answers[element.element_id]?.pre_grade?.score != null &&
        (answers[element.element_id].pre_grade.score > 0 ? (
          answers[element.element_id].pre_grade?.comment ? (
            <details className="inline-block align-middle mr-2">
              <summary className="text-sm select-none text-green-500">
                [Предварительно верно]
              </summary>
              <span className="block p-2 text-sm opacity-60">
                {answers[element.element_id].pre_grade?.comment}
              </span>
            </details>
          ) : (
            <span className="text-sm text-green-500 mr-2">
              [Предварительно верно]
            </span>
          )
        ) : (
          <details className="inline-block align-middle mr-2">
            <summary className="text-sm select-none text-red-500">
              [Предварительно неверно]
            </summary>
            <span className="block p-2 text-sm opacity-60">
              {answers[element.element_id].pre_grade?.comment}
            </span>
          </details>
        ))}

      <span
        className={`inline-block align-middle ${
          element.properties?.simple ? "w-full max-w-xs" : "w-full mt-4"
        }`}
      >
        {element.properties?.simple ? (
          <input
            type="text"
            className={`bg-transparent border-b w-full transition-colors duration-150 focus:outline-none ${
              isRight === true
                ? "border-green-500 bg-green-500/10"
                : isRight === false
                ? "border-red-500 bg-red-500/10"
                : "border-zinc-500 focus:border-zinc-200"
            }`}
            placeholder={graderView ? "Нет ответа" : "Ваш ответ"}
            value={answers[element.element_id]?.data?.text ?? ""}
            onChange={onChangeAnswer}
            disabled={!editable}
          />
        ) : (
          <Textarea
            className={`block bg-transparent border rounded-xl w-full p-4 transition-colors duration-150 ${
              isRight === true
                ? "border-green-500"
                : isRight === false
                ? "border-red-500 bg-red-500/10"
                : "border-zinc-700 focus:border-zinc-400"
            }`}
            placeholder={graderView ? "Нет ответа" : "Ваш ответ"}
            minRowsCount={5}
            onChange={onChangeAnswer}
            value={answers[element.element_id]?.data?.text ?? ""}
            disabled={!editable}
          />
        )}
      </span>

      {!editable &&
        answers &&
        (answers[element.element_id]?.given_score != null ||
          answers?.data == null) && (
          <span className="ml-3 text-sm font-bold align-middle opacity-80">
            {score > 0 ? "✔️" : "❌"}
            {score * element.properties.weight} / {element.properties.weight}
          </span>
        )}

      {graderView && (
        <span className="inline-flex items-center ml-4 gap-2 align-middle">
          {answers[element.element_id]?.given_score != null && (
            <span className="text-xs opacity-50 mr-1">Новая оценка:</span>
          )}
          <button
            type="button"
            className={`text-2xl transition-opacity ${
              isRight === true ||
              (isRight === null &&
                (answers[element.element_id]?.pre_grade == null ||
                  answers[element.element_id]?.pre_grade?.score > 0))
                ? "opacity-100"
                : "opacity-20 hover:opacity-50"
            }`}
            onClick={() => changeScore(1)}
          >
            ✔️
          </button>
          <button
            type="button"
            className={`text-2xl transition-opacity ${
              isRight === false ||
              (isRight === null &&
                (answers[element.element_id]?.pre_grade == null ||
                  answers[element.element_id]?.pre_grade?.score === 0))
                ? "opacity-100"
                : "opacity-20 hover:opacity-50"
            }`}
            onClick={() => changeScore(0)}
          >
            ❌
          </button>
        </span>
      )}

      {editable && !graderView && (
        <span className="text-[11px] opacity-40 ml-2 align-middle font-medium">
          (max: {element.properties.weight})
        </span>
      )}
    </span>
  );
};

export default AnswerComponent;
