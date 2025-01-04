import { TextElement } from "../../model/templateElement";
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
  <p className={`mb-3 ${getMarginLeftStyle(element.properties.nestingLevel)}`}>
    {element.properties?.numberingBulletText && (
      <span>{element.properties.numberingBulletText + " "}</span>
    )}
    {element.properties.data}
  </p>
);

export default TextComponent;
