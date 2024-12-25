import React from "react";
import { TemplateModel, TemplateElement } from "../../actions/dto/template";
import TextQuestionComponent from "../../components/Template/TextQuestionComponent";
import ImageComponent from "../../components/Template/ImageComponent";
import HeaderComponent from "../../components/Template/HeaderComponent";
import TableComponent from "../../components/Template/TableComponent";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import AnswerComponent from "../../components/Template/AnswerComponent";
import { useLoaderData } from "react-router";

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
  const template: TemplateModel = useLoaderData();

  return (
    <div>
      <input
        className="text-3xl font-medium text-center mb-10 w-full
        bg-transparent border-b border-zinc-200 dark:border-zinc-950
        focus-visible:outline-none focus-visible:border-zinc-950 dark:focus-visible:border-zinc-200"
        defaultValue={template.name}
      />
      <p>
        Максимальное количество баллов:
        <input
          type="number"
          min="0"
          defaultValue={template.max_score}
          className="w-20 bg-transparent border-b focus-visible:outline-none border-zinc-950 dark:border-zinc-200 mb-4"
        />
      </p>
      {template?.elements.map((element) => (
        <React.Fragment key={element.element_id}>
          {renderElement(element.properties)}
          {element.element_type === "question" && <AnswerComponent />}
        </React.Fragment>
      ))}
      {/* Ни в коем случае не удаляйте этот элемент, так как не будут сгенерированы нужные классы отступов и размеров заголовков*/}
      <span className="ml-4 ml-8 ml-12 ml-16 ml-20 ml-24 ml-28 ml-32 ml-36 ml-40 text-3xl text-2xl"></span>
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
