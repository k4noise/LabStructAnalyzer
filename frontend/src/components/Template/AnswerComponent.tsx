import React, { useContext, useState, useEffect, useCallback } from "react";
import { AnswerElement } from "../../model/templateElement";
import AnswerContext, { AnswerContextProps } from "../../context/AnswerContext";
import Button from "../Button/Button";
import Textarea from "../Textarea/TextareaComponent";
import { api } from "../../utils/sendRequest";

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

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
    hintLink,
  } = useContext(AnswerContext);

  const [hintText, setHintText] = useState<string | null>(null);
  const currentAnswerData = answers?.[element.id];
  const currentAnswerText = currentAnswerData?.data?.text ?? "";

  const debouncedText = useDebounce(currentAnswerText, 500);

  const score = currentAnswerData?.score ?? null;

  useEffect(() => {
    const currentAnswer = answers?.[element.id];
    if (currentAnswer?.score != null) {
      setIsRight(currentAnswer.score > 0);
    } else if (currentAnswer?.pre_grade?.score != null) {
      setIsRight(currentAnswer.pre_grade.score > 0);
    } else {
      setIsRight(null);
    }
  }, [answers, element.id]);

  const fetchHint = useCallback(
    async (text: string) => {
      if (!hintLink) {
        setHintText(null);
        return;
      }

      setHintText(null);

      try {
        const requestBody = {
          question_id: element.id,
          current: {
            element_id: element.id,
            data: { text: text },
          },
          params: [],
        };

        const response = await api.post(hintLink, requestBody);

        const receivedHint = response.data;
        setHintText(
          receivedHint
            ? String(receivedHint)
            : "Подсказка найдена, но текст не предоставлен."
        );
      } catch (error) {
        console.error("Ошибка при получении подсказки:", error);
        setHintText("Не удалось загрузить подсказку.");
      }
    },
    [hintLink, element.id, answers]
  );

  useEffect(() => {
    if (
      editable &&
      !graderView &&
      debouncedText &&
      debouncedText !== currentAnswerText
    ) {
      fetchHint(debouncedText);
    } else if (!editable || graderView || !debouncedText) {
      setHintText(null);
    }
  }, [debouncedText, editable, graderView, fetchHint, currentAnswerText]);

  const onChangeAnswer = (e: any) => {
    updateAnswer({
      id: element.id,
      data: { text: e.target.value },
    });
  };

  const changeScore = (score: number) => {
    setIsRight(score !== 0);
    updateAnswer({
      id: element.id,
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
    <span className="not-italic inline-flex items-baseline flex-wrap gap-y-2">
      {!graderView && element.properties.data && (
        <details className="inline-grid mr-4 align-middle relative">
          <summary className="text-base select-none cursor-pointer opacity-60 hover:opacity-100">
            [Подсказка]
          </summary>
          <span className="absolute left-0 top-full mt-1 max-w-lg truncate bg-zinc-200 dark:bg-zinc-900 text-sm px-2 py-1 rounded shadow-lg z-50">
            {element.properties.data}
          </span>
        </details>
      )}

      {graderView &&
        currentAnswerData?.pre_grade?.score != null &&
        (currentAnswerData.pre_grade.score > 0 ? (
          currentAnswerData.pre_grade?.comment ? (
            <details className="inline-block align-middle mr-2 relative">
              <summary className="text-sm select-none text-green-500 cursor-pointer">
                [Предварительно верно]
              </summary>
              <span className="absolute left-0 top-full block p-2 text-sm bg-zinc-800 rounded shadow-md z-50 min-w-[200px]">
                {currentAnswerData.pre_grade?.comment}
              </span>
            </details>
          ) : (
            <span className="text-sm text-green-500 mr-2">
              [Предварительно верно]
            </span>
          )
        ) : (
          <details className="inline-block align-middle mr-2 relative">
            <summary className="text-sm select-none text-red-500 cursor-pointer">
              [Предварительно неверно]
            </summary>
            <span className="absolute left-0 top-full block p-2 text-sm bg-zinc-800 rounded shadow-md z-50 min-w-[200px]">
              {currentAnswerData.pre_grade?.comment}
            </span>
          </details>
        ))}

      <span
        className={`inline-flex flex-col align-middle ml-2 ${
          element.properties?.simple ? "w-full max-w-xs" : "w-full mt-4"
        }`}
      >
        <input
          type="text"
          className={`bg-transparent border-b w-full transition-colors duration-150 focus:outline-none py-1 ${
            isRight === true
              ? "border-green-500 bg-green-500/10"
              : isRight === false
              ? "border-red-500 bg-red-500/10"
              : "border-zinc-500 focus:border-zinc-200"
          }`}
          placeholder={graderView ? "Нет ответа" : "Ваш ответ"}
          value={currentAnswerText}
          onChange={onChangeAnswer}
          disabled={!editable}
        />

        {editable && !graderView && hintText && (
          <div className="mt-2 p-3 bg-yellow-100 border-l-4 border-yellow-500 text-sm rounded dark:bg-yellow-900/30 dark:border-yellow-400">
            <strong>Подсказка:</strong> {hintText}
          </div>
        )}

        {editable && !graderView && (
          <span className="text-[10px] opacity-40 font-medium mt-1 leading-none">
            (max: {element.properties.weight})
          </span>
        )}
      </span>

      {!editable &&
        currentAnswerData &&
        (currentAnswerData?.given_score != null ||
          currentAnswerData?.data == null) && (
          <span className="ml-3 text-sm font-bold align-middle opacity-80 whitespace-nowrap self-center">
            {score > 0 ? "✔️" : "❌"}
            {score * element.properties.weight} / {element.properties.weight}
          </span>
        )}

      {graderView && (
        <span className="inline-flex items-center ml-4 gap-2 align-middle self-center">
          {currentAnswerData?.given_score != null && (
            <span className="text-xs opacity-50 mr-1">Новая оценка:</span>
          )}
          <button
            type="button"
            className={`text-2xl transition-all hover:scale-110 active:scale-90 ${
              isRight === true ||
              (isRight === null &&
                (currentAnswerData?.pre_grade == null ||
                  currentAnswerData?.pre_grade?.score > 0))
                ? "opacity-100"
                : "opacity-20 hover:opacity-50"
            }`}
            onClick={() => changeScore(1)}
          >
            ✔️
          </button>
          <button
            type="button"
            className={`text-2xl transition-all hover:scale-110 active:scale-90 ${
              isRight === false ||
              (isRight === null &&
                (currentAnswerData?.pre_grade == null ||
                  currentAnswerData?.pre_grade?.score === 0))
                ? "opacity-100"
                : "opacity-20 hover:opacity-50"
            }`}
            onClick={() => changeScore(0)}
          >
            ❌
          </button>
        </span>
      )}
    </span>
  );
};

export default AnswerComponent;
