import { HeaderElement } from "../../actions/dto/template";
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
  const Tag = `h${element.headerLevel ?? 3}` as keyof JSX.IntrinsicElements;
  const numberingText = element.numberingBulletText;
  return (
    <Tag className={`font-medium ${getMarginLeftStyle(element.nestingLevel)}`}>
      {numberingText ? `${numberingText} ${element.data}` : element.data}
    </Tag>
  );
};

export default HeaderComponent;
