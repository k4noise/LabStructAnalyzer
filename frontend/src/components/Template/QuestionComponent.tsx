import React from "react";
import { QuestionElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import { ParentElementProps } from "./TemplateElements";

const QuestionComponent: React.FC<ParentElementProps<QuestionElement>> = ({
  element,
  children,
  renderChild,
}) => {
  const answerChild = children.find((child) => child.type === "answer");
  const otherChildren = children.filter((child) => child.type !== "answer");

  return (
    <div
      className={`my-8 ${getMarginLeftStyle(element.properties.nestingLevel)} ${
        answerChild?.properties.editNow
          ? "dark:text-blue-300 text-blue-600"
          : ""
      }`}
    >
      <div className="mb-2">
        {element.properties.numberingBulletText && (
          <span className="font-bold mr-2">
            {element.properties.numberingBulletText}
          </span>
        )}
        <span className="italic">{element.properties.data}</span>
      </div>

      {otherChildren.length > 0 && (
        <div className="mb-4">{otherChildren.map(renderChild)}</div>
      )}

      {answerChild && (
        <div className="not-italic">{renderChild(answerChild)}</div>
      )}
    </div>
  );
};

export default QuestionComponent;
