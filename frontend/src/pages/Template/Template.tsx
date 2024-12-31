import React from "react";
import {
  TemplateModel,
  TemplateElement,
  TemplateElementModel,
} from "../../model/template";
import TextComponent from "../../components/Template/TextComponent";
import ImageComponent from "../../components/Template/ImageComponent";
import HeaderComponent from "../../components/Template/HeaderComponent";
import TableComponent from "../../components/Template/TableComponent";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import AnswerComponent from "../../components/Template/AnswerComponent";
import { useLoaderData } from "react-router";
import BackButtonComponent from "../../components/BackButtonComponent";
import QuestionAnswerComponent from "../../components/Template/QuestionAnswerComponent";

/**
 * Карта соответствий типов элементов и компонентов для рендеринга.
 *
 * @constant
 * @type {Record<string, React.FC<any>>}
 */
const componentMap: Record<string, React.FC<{ element: TemplateElement }>> = {
  text: TextComponent,
  image: ImageComponent,
  header: HeaderComponent,
  question: QuestionAnswerComponent,
  table: TableComponent,
  answer: AnswerComponent,
};

/**
 * Основной компонент шаблона, отображающий различные элементы.
 */
const Template: React.FC = () => {
  const { data: template } = useLoaderData<{ data: TemplateModel }>();

  return (
    <div>
      <BackButtonComponent positionClasses="" />
      <input
        className="text-3xl font-medium text-center mt-12 mb-10 w-full
        bg-transparent border-b border-zinc-200 dark:border-zinc-950
        focus-visible:outline-none focus-visible:border-zinc-950 dark:focus-visible:border-zinc-200"
        defaultValue={template.name}
      />
      <p className="opacity-60">
        Максимальное количество баллов:
        <input
          type="number"
          min="0"
          defaultValue={template.max_score}
          className="w-20 mb-4 ml-3 bg-transparent border-b focus-visible:outline-none border-zinc-950 dark:border-zinc-200"
        />
      </p>
      {template?.elements.map((element) => renderElement(element))}
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
const renderElement = (element: TemplateElementModel): React.ReactNode => {
  const Component = componentMap[element.type] || null;
  if (Component) {
    return <Component element={element.properties} />;
  }

  if (Array.isArray(element.properties.data)) {
    return (
      <div
        className={`my-5 ${getMarginLeftStyle(
          element.properties.nestingLevel ?? 1
        )}`}
      >
        {element.properties.data.map((childElement) =>
          renderElement(childElement)
        )}
      </div>
    );
  }

  return null;
};

export default Template;
export { renderElement };
