import { TextElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";

interface TextComponentProps {
  element: TextElement;
}

const TextComponent: React.FC<TextComponentProps> = ({ element }) => (
  <p className={`mb-3 ${getMarginLeftStyle(element.properties.nestingLevel)}`}>
    {element.properties?.numberingBulletText && (
      <span>{element.properties.numberingBulletText + " "}</span>
    )}
    {element.properties.data}
  </p>
);

export default TextComponent;
