import { memo } from "react";
import { TemplateElementModel } from "../../model/templateElement";
import AnswerComponent from "./AnswerComponent";
import HeaderComponent from "./HeaderComponent";
import ImageComponent from "./ImageComponent";
import QuestionAnswerComponent from "./QuestionAnswerComponent";
import TableComponent from "./TableComponent";
import TextComponent from "./TextComponent";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import AnswerContext, { AnswerContextProps } from "../../context/AnswerContext";

/**
 * Карта соответствий типов элементов и компонентов для рендеринга.
 *
 * @constant
 * @type {Record<string, React.FC<any>>}
 */
const componentMap: Record<
  string,
  React.FC<{ element: TemplateElementModel }>
> = {
  text: memo(TextComponent),
  image: memo(ImageComponent),
  header: memo(HeaderComponent),
  question: QuestionAnswerComponent,
  table: memo(TableComponent),
  answer: AnswerComponent,
};

const renderElement = (element: TemplateElementModel): React.ReactNode => {
  const Component = componentMap[element.element_type] || null;

  const marginLeftStyle = getMarginLeftStyle(element.properties.nestingLevel);

  if (Component) {
    return <Component element={element} key={element.element_id} />;
  }

  if (Array.isArray(element.properties.data)) {
    return (
      <div className={`my-5 ${marginLeftStyle}`} key={element.element_id}>
        {element.properties.data.map(renderElement)}
      </div>
    );
  }

  return null;
};

interface TemplateElementsProps {
  elements: TemplateElementModel[];
  answerContextProps: AnswerContextProps;
}

const TemplateElements: React.FC<TemplateElementsProps> = ({
  elements,
  answerContextProps,
}) => {
  return (
    <AnswerContext.Provider value={answerContextProps}>
      {elements.map(renderElement)}
      {/* Ни в коем случае не удаляйте этот элемент, так как не будут сгенерированы нужные классы отступов и размеров заголовков*/}
      <span className="ml-4 ml-8 ml-12 ml-16 ml-20 ml-24 ml-28 ml-32 ml-36 ml-40 my-4 my-8 my-12 my-16 my-20 text-3xl text-2xl"></span>
    </AnswerContext.Provider>
  );
};

export default TemplateElements;
export { renderElement };
