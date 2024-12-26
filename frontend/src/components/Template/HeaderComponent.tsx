import { HeaderElement } from "../../api/dto/template";
import { getMarginLeftStyle } from "../../utils/templateStyle";

/**
 * Свойства для компонента HeaderComponent.
 *
 * @interface HeaderComponentProps
 * @property {HeaderElement} element - Элемент заголовка.
 */
interface HeaderComponentProps {
  element: HeaderElement;
}

/**
 * Компонент для отображения заголовка.
 *
 * @param {HeaderComponentProps} props - Свойства компонента.
 */
const HeaderComponent: React.FC<HeaderComponentProps> = ({ element }) => {
  const Tag = `h${element.headerLevel}` as keyof JSX.IntrinsicElements;
  const numberingText = element.numberingBulletText;
  return (
    <Tag
      className={`font-medium mb-5 ${getMarginLeftStyle(
        element.nestingLevel
      )} ${
        4 - element.headerLevel > 0 ? `text-${4 - element.headerLevel}xl` : ""
      }`}
    >
      {numberingText ? `${numberingText} ${element.data}` : element.data}
    </Tag>
  );
};

export default HeaderComponent;
