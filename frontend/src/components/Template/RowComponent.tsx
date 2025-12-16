import React from "react";
import { ParentElementProps } from "./TemplateElements";

const RowComponent: React.FC<ParentElementProps<any>> = ({
  children,
  renderChild,
}) => {
  return <tr>{children.map(renderChild)}</tr>;
};

export default RowComponent;
