import React from "react";
import { TableElement } from "../../model/templateElement";
import { renderElement } from "../../pages/Template/Template";
import { getMarginLeftStyle } from "../../utils/templateStyle";

interface TableProps {
  element: TableElement;
}

const TableComponent: React.FC<TableProps> = ({ element }) => {
  return (
    <table
      className={`border-collapse ${getMarginLeftStyle(
        element.properties.nestingLevel
      )}`}
    >
      <tbody>
        {element.properties.data.map((row) => (
          <tr key={row.element_id}>
            {row.properties?.data?.map((cell) => {
              const isMerged = cell.properties?.merged;
              const rowSpan = isMerged && cell.properties?.cols;
              const colSpan = isMerged && cell.properties?.rows;

              return (
                <td
                  key={cell.element_id}
                  rowSpan={rowSpan}
                  colSpan={colSpan}
                  className="border-2 p-2 border-zinc-950 dark:border-zinc-200"
                >
                  {cell.properties?.data?.map((nestedElement) =>
                    renderElement(nestedElement)
                  )}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default TableComponent;
