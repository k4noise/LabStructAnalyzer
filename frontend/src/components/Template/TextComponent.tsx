import { TextElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import { BaseElementProps } from "./TemplateElements";

interface TextComponentProps extends BaseElementProps<TextElement> {}

const TextComponent: React.FC<TextComponentProps> = ({ element, level }) => (
  <p className={`mb-3 ${getMarginLeftStyle(level)}`}>
    {element.properties?.numberingBulletText && (
      <span>{element.properties.numberingBulletText + " "}</span>
    )}
    {element.properties.data}
  </p>
);

export default TextComponent;
