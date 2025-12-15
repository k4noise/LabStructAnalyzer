import { HeaderElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";

interface HeaderComponentProps {
  element: HeaderElement;
  level: number;
  children: any[];
  renderChild: (child: any) => React.ReactNode;
}

const HeaderComponent: React.FC<HeaderComponentProps> = ({
  element,
  level,
}) => {
  const Tag =
    `h${element.properties.headerLevel}` as keyof JSX.IntrinsicElements;
  const numberingText = element.properties.numberingBulletText;
  return (
    <Tag
      className={`font-bold ${getMarginLeftStyle(level)} ${
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
