import { TableElement } from "../../model/template";
import { renderElement } from "../../pages/Template/Template";
import { getMarginLeftStyle } from "../../utils/templateStyle";

/**
 * Свойства для компонента TableComponent.
 *
 * @interface TableProps
 * @property {TableElement} element - Элемент таблицы.
 */
interface TableProps {
  element: TableElement;
}

/**
 * Компонент для отображения таблицы.
 *
 * @param {TableProps} props - Свойства компонента.
 * @returns {JSX.Element} Элемент таблицы с данными.
 */
const TableComponent: React.FC<TableProps> = ({ element }) => {
  return (
    <table
      className={`border-collapse ${getMarginLeftStyle(element.nestingLevel)}`}
    >
      <tbody>
        {element.data.map((row) => (
          <tr key={row.id}>
            {row.properties?.data?.map((cell) => {
              const isMerged = cell.properties?.merged;
              const rowSpan = isMerged && cell.properties?.cols;
              const colSpan = isMerged && cell.properties?.rows;

              return (
                <td
                  key={cell.id}
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
