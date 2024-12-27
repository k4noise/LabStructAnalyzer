import { QuestionElement, TextElement } from "../../model/template";
import { getMarginLeftStyle } from "../../utils/templateStyle";

/**
 * Свойства для компонента TextBlockComponent.
 *
 * @interface TextBlockProps
 * @property {TextElement | QuestionElement} element - Элемент текста или вопроса.
 */
interface TextBlockProps {
  element: TextElement | QuestionElement;
}

/**
 * Компонент для отображения текстового блока или вопроса.
 *
 * @param {TextBlockProps} props - Свойства компонента.
 */
const TextQuestionComponent: React.FC<TextBlockProps> = ({ element }) => {
  const isQuestion = (element.type as "text" | "question") === "question";
  const className = `${
    isQuestion ? "italic inline-block my-3" : "mb-3"
  } ${getMarginLeftStyle(element.nestingLevel)}`;

  return (
    <p className={className}>
      {element.numberingBulletText && (
        <span>{element.numberingBulletText + " "}</span>
      )}
      {element.data}
    </p>
  );
};

export default TextQuestionComponent;
