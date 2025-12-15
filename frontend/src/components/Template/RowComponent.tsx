import React from "react";
import { BaseElementProps } from "./TemplateElements";

const RowComponent: React.FC<BaseElementProps<any>> = ({
  children,
  renderChild,
}) => {
  return (
    <tr>
      {children.map(renderChild)}
    </tr>
  );
};

export default RowComponent;
