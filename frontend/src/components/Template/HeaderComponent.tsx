import { HeaderElement } from "../../model/template";
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
  const Tag =
    `h${element.properties.headerLevel}` as keyof JSX.IntrinsicElements;
  const numberingText = element.properties.numberingBulletText;
  return (
    <Tag
      className={`font-medium mb-5 ${getMarginLeftStyle(
        element.properties.nestingLevel
      )} ${
        4 - element.properties.headerLevel > 0
          ? `text-${4 - element.properties.headerLevel}xl`
          : ""
      }`}
    >
      {numberingText
        ? `${numberingText} ${element.properties.data}`
        : element.properties.data}
    </Tag>
  );
};

export default HeaderComponent;
