import { TableElement } from "../../api/dto/template";
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
const TableComponent: React.FC<TableProps> = ({ element }) => (
  <table
    className={`border-collapse ${getMarginLeftStyle(element.nestingLevel)}`}
  >
    <tbody>
      {element.data.map((row, rowIndex) => (
        <tr key={rowIndex}>
          {row.map((cell, cellIndex) => {
            const isMerged = cell?.merged;
            const rowSpan = isMerged && cell?.cols;
            const colSpan = isMerged && cell?.rows;

            return (
              <td
                key={`${rowIndex}-${cellIndex}`}
                rowSpan={rowSpan}
                colSpan={colSpan}
                className="border-2 p-2 border-zinc-950 dark:border-zinc-200"
              >
                {cell.data?.map((nestedElement) =>
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

export default TableComponent;
