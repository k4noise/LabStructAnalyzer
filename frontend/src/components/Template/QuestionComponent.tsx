import React from "react";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import { ParentElementProps } from "./TemplateElements";

const QuestionComponent: React.FC<ParentElementProps<any>> = ({
  element,
  children,
  renderChild,
}) => {
  const answerChild = children.find((c) => c.type === "answer");
  const isEditing = answerChild?.properties.editNow;

  return (
    <div
      className={`
        my-12 italic leading-relaxed
        ${getMarginLeftStyle(element.properties.nestingLevel)}
        ${isEditing ? "text-blue-400" : "text-zinc-100"}
        text-xl font-medium`}
    >
      <div className="flex flex-wrap items-baseline gap-x-2">
        {children.map(renderChild)}
      </div>
    </div>
  );
};

export default QuestionComponent;
