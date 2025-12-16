import { HeaderElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";

interface HeaderComponentProps {
  element: HeaderElement;
}

const HeaderComponent: React.FC<HeaderComponentProps> = ({ element }) => {
  const Tag =
    `h${element.properties.headerLevel}` as keyof JSX.IntrinsicElements;
  const numberingText = element.properties.numberingBulletText;
  return (
    <Tag
      className={`font-bold ${getMarginLeftStyle(
        element.properties.nestingLevel
      )} ${
        4 - element.properties.headerLevel > 0
          ? `text-${4 - element.properties.headerLevel}xl my-${
              4 * (4 - element.properties.headerLevel)
            }`
          : "my-4"
      }`}
    >
      {numberingText
        ? `${numberingText} ${element.properties.data}`
        : element.properties.data}
    </Tag>
  );
};

export default HeaderComponent;
