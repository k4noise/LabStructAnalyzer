import { TextElement } from "../../model/template";
import { getMarginLeftStyle } from "../../utils/templateStyle";

/**
 * Свойства для компонента TextComponent.
 *
 * @interface TextBlockProps
 * @property {TextElement} element - Элемент текста.
 */
interface TextBlockProps {
  element: TextElement;
}

/**
 * Компонент для отображения текстового блока или вопроса.
 *
 * @param {TextBlockProps} props - Свойства компонента.
 */
const TextComponent: React.FC<TextBlockProps> = ({ element }) => (
  <p className={`mb-3 ${getMarginLeftStyle(element.nestingLevel)}`}>
    {element.numberingBulletText && (
      <span>{element.numberingBulletText + " "}</span>
    )}
    {element.data}
  </p>
);

export default TextComponent;
