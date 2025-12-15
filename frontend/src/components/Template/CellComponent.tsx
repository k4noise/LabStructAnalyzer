import React from "react";


interface CellProps {
  element: any;
  level: number;
  children: any[];
  renderChild: (child: any) => React.ReactNode;
}

const CellComponent: React.FC<CellProps> = ({
  element,
  children,
  renderChild,
}) => {
  const isMerged = element.properties?.merged;
  const rowSpan = isMerged && element.properties?.rows;
  const colSpan = isMerged && element.properties?.cols;

  return (
    <td
      rowSpan={rowSpan}
      colSpan={colSpan}
      className="border-2 p-2 border-zinc-950 dark:border-zinc-200"
    >
      {children.map(renderChild)}
    </td>
  );
};

export default CellComponent;
