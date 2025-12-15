import React from "react";
import { QuestionElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import { BaseElementProps } from "./TemplateElements";

const QuestionComponent: React.FC<BaseElementProps<QuestionElement>> = ({
  element,
  level,
  children,
  renderChild,
}) => {

  const answerChild = children.find((child) => child.type === "answer");

  return (
    <div
      className={`italic my-8 ${getMarginLeftStyle(level)} ${
        answerChild?.properties.editNow
          ? "dark:text-blue-300 text-blue-600"
          : ""
      }`}
    >
      <p>
        {element.properties.numberingBulletText && (
          <span>{element.properties.numberingBulletText + " "}</span>
        )}
        {element.properties.data}
        {answerChild && (
          <span className="ml-4 inline">
            {renderChild(answerChild)}
          </span>
        )}
      </p>
    </div>
  );
};

export default QuestionComponent;
