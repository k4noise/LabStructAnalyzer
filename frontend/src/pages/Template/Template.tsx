import React from "react";
import { TemplateElement } from "../../actions/dto/template";
import TextQuestionComponent from "../../components/Template/TextQuestionComponent";
import ImageComponent from "../../components/Template/ImageComponent";
import HeaderComponent from "../../components/Template/HeaderComponent";
import TableComponent from "../../components/Template/TableComponent";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import AnswerComponent from "../../components/Template/AnswerComponent";

/**
 * Карта соответствий типов элементов и компонентов для рендеринга.
 *
 * @constant
 * @type {Record<string, React.FC<any>>}
 */
const componentMap: Record<string, React.FC<{ element: TemplateElement }>> = {
  text: TextQuestionComponent,
  image: ImageComponent,
  header: HeaderComponent,
  question: TextQuestionComponent,
  table: TableComponent,
};

/**
 * Основной компонент шаблона, отображающий различные элементы.
 */
const Template: React.FC = () => {
  const dataStr = localStorage.getItem("pageData");
  const data: TemplateElement[] = dataStr ? JSON.parse(dataStr) : [];

  return (
    <div>
      <h2 className="text-3xl font-medium text-center mb-10">
        Новая лабораторная работа
      </h2>
      {data.map((element, index) => (
        <React.Fragment key={element.id || index}>
          {renderElement(element)}
          {element.type === "question" && <AnswerComponent />}
        </React.Fragment>
      ))}
    </div>
  );
};

/**
 * Рендерит элемент шаблона на основе его типа.
 *
 * @param {TemplateElement} element - Элемент шаблона для рендеринга.
 */
const renderElement = (element: TemplateElement): React.ReactNode => {
  const Component = componentMap[element.type] || null;

  if (Component) {
    return <Component element={element} />;
  }

  if (Array.isArray(element.data)) {
    return (
      <div className={`my-5 ${getMarginLeftStyle(element.nestingLevel ?? 1)}`}>
        {element.data.map((childElement, index) => (
          <React.Fragment key={index}>
            {renderElement(childElement)}
          </React.Fragment>
        ))}
      </div>
    );
  }

  return null;
};

export default Template;
export { renderElement };
