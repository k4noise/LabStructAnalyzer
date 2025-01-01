import { QuestionElement } from "../../model/template";
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
      className={`italic my-3 ${getMarginLeftStyle(
        element.properties.nestingLevel
      )}`}
    >
      <p>
        {question.properties.numberingBulletText && (
          <span>{question.properties.numberingBulletText + " "}</span>
        )}
        {question.properties.data}
        <AnswerComponent element={answer} />
      </p>
    </div>
  );
};

export default QuestionAnswerComponent;
