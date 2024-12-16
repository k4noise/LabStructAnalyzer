import React from "react";
import {
  CompositeElement,
  HeaderElement,
  ImageElement,
  QuestionElement,
  TableElement,
  TemplateElement,
  TextElement,
} from "../../actions/dto/template";

export const Template = () => {
  const dataStr = localStorage.getItem("pageData");
  let data = [];

  try {
    if (dataStr) {
      data = JSON.parse(dataStr) || [];
    }
  } catch (e) {
    console.error("Failed to parse pageData", e);
  }

  return (
    <div>
      <h2 className="text-3xl font-medium text-center mb-10">
        Новая лабораторная работа
      </h2>
      {data.map((element: TemplateElement) => TemplateFactory(element))}
      <span className="ml-4 ml-8 ml-12 ml-16 ml-20 ml-24 ml-28 ml-32 ml-36"></span>
    </div>
  );
};

const TemplateFactory: React.FC = (element: TemplateElement) => {
  switch (element?.type) {
    case "text":
      return <TextComponent element={element as TextElement} />;
    case "image":
      return <ImageComponent element={element as ImageElement} />;
    case "header":
      return <HeaderComponent element={element as HeaderElement} />;
    case "question":
      return <QuestionComponent element={element as QuestionElement} />;
    case "answer":
      return <AnswerComponent />;
    case "table":
      return <TableComponent element={element as TableElement} />;
    default:
      if (element && Array.isArray(element.data)) {
        return <CompositeComponent element={element as CompositeElement} />;
      }
      return null;
  }
};

const getMarginLeftStyle = (level: number = 0): string => {
  const base = level * 4;
  return `ml-${base}`;
};

const TextComponent: React.FC<{ element: TextElement }> = ({ element }) => {
  if (element.numberingBulletText) {
    return (
      <p className={getMarginLeftStyle(element.nestingLevel)}>
        {element.numberingBulletText && (
          <span>{element.numberingBulletText + " "}</span>
        )}
        {element.data}
      </p>
    );
  } else {
    return (
      <p className={getMarginLeftStyle(element.nestingLevel)}>{element.data}</p>
    );
  }
};

const ImageComponent: React.FC<{ element: ImageElement }> = ({ element }) => (
  <img src={element.data} alt="" className="mx-auto" />
);

const HeaderComponent: React.FC<{ element: HeaderElement }> = ({ element }) => {
  const Tag = `h${element.headerLevel ?? 3}` as keyof JSX.IntrinsicElements;
  return (
    <Tag className={`font-medium ${getMarginLeftStyle(element.nestingLevel)}`}>
      {element.numberingBulletText && (
        <span>{element.numberingBulletText + " "}</span>
      )}
      {element.numberingHeaderText
        ? `${element.numberingHeaderText} ${element.data}`
        : element.data}
    </Tag>
  );
};

const QuestionComponent: React.FC<{ element: QuestionElement }> = ({
  element,
}) => (
  <span
    className={`italic inline-block my-3 ${getMarginLeftStyle(
      element.nestingLevel
    )}`}
  >
    {element.numberingBulletText && (
      <span>{element.numberingBulletText + " "}</span>
    )}
    {element.data}
  </span>
);

const AnswerComponent: React.FC = () => (
  <>
    <button className="px-2 py-1 ml-2 mb-2 border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950">
      Настройка ответа
    </button>
    <br />
  </>
);

const TableComponent: React.FC<{ element: TableElement }> = ({ element }) => (
  <table
    className={`border-collapse ${getMarginLeftStyle(element.nestingLevel)}`}
  >
    <tbody>
      {element.data.map((row, rowIndex) => (
        <tr key={rowIndex}>
          {row.map((cell, cellIndex) => {
            const isMerged = cell?.merged;
            const rowSpan = isMerged && cell?.cols;
            const colSpan = isMerged && cell?.rows;

            return (
              <td
                key={`${rowIndex}-${cellIndex}`}
                rowSpan={rowSpan}
                colSpan={colSpan}
                className="border-2 p-2 border-zinc-950 dark:border-zinc-200"
              >
                {cell.data.map((nestedElement) =>
                  TemplateFactory(nestedElement)
                )}
              </td>
            );
          })}
        </tr>
      ))}
    </tbody>
  </table>
);

const CompositeComponent: React.FC<{ element: CompositeElement }> = ({
  element,
}) => (
  <div className={`my-5 ${getMarginLeftStyle(element.nestingLevel)}`}>
    {element.data.map((childElement: TemplateElement) =>
      TemplateFactory(childElement)
    )}
  </div>
);
