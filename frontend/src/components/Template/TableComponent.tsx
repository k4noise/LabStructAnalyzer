import React from "react";
import { TableElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";
import { BaseElementProps } from "./TemplateElements";

const TableComponent: React.FC<BaseElementProps<TableElement>> = ({
  element,
  level,
  children,
  renderChild,
}) => {
  return (
    <table className={`border-collapse ${getMarginLeftStyle(level)}`}>
      <tbody>
        {children.map(renderChild)}
      </tbody>
    </table>
  );
};

export default TableComponent;
