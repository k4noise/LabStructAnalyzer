import React from "react";
import { ParentElementProps } from "./TemplateElements";

const CellComponent: React.FC<ParentElementProps<any>> = ({
  element,
  children,
  renderChild,
}) => {
  const isMerged = element.properties?.merged;

  const rowSpan = isMerged ? element.properties?.cols : undefined;
  const colSpan = isMerged ? element.properties?.rows : undefined;

  return (
    <td
      rowSpan={rowSpan}
      colSpan={colSpan}
      className="border-2 p-3 border-zinc-950 dark:border-zinc-200 align-top min-w-[100px]"
    >
      {children.map(renderChild)}
    </td>
  );
};

export default CellComponent;
