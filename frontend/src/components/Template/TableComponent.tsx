import React from "react";
import { TableElement } from "../../model/templateElement";
import { ParentElementProps } from "./TemplateElements";

const TableComponent: React.FC<ParentElementProps<TableElement>> = ({
  children,
  renderChild,
}) => {
  return (
    <div className="w-full overflow-x-auto my-6">
      <table className="border-collapse mx-auto">
        <tbody>{children.map(renderChild)}</tbody>
      </table>
    </div>
  );
};

export default TableComponent;
