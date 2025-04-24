import { QuestionElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import AnswerComponent from "./AnswerComponent";

/**
 * Свойства для компонента QuestionAnswerComponent.
 *
 * @interface TextBlockProps
 * @property {TextElement} element - Элемент вопроса.
 */
interface QuestionAnswerProps {
  element: QuestionElement;
}

/**
 * Компонент для отображения текстового блока или вопроса.
 *
 * @param {QuestionAnswerProps} props - Свойства компонента.
 */
const QuestionAnswerComponent: React.FC<QuestionAnswerProps> = ({
  element,
}) => {
  const [question, answer] = element.properties.data;
  return (
    <div
      className={`italic my-6 ${getMarginLeftStyle(
        element.properties.nestingLevel
      )} ${
        answer.properties.editNow ? "dark:text-blue-300 text-blue-600" : ""
      }`}
    >
      <p>
        {question.properties.numberingBulletText && (
          <span>{question.properties.numberingBulletText + " "}</span>
        )}
        {question.properties.data}
        <span className="ml-4 inline">
          <AnswerComponent element={answer} />
        </span>
      </p>
    </div>
  );
};

export default QuestionAnswerComponent;
