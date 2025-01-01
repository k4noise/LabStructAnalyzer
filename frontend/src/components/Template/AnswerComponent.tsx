import { AnswerElement } from "../../model/template";

/**
 * Свойства для компонента ImageComponent.
 *
 * @interface ImageComponentProps
 * @property {ImageElement} element - Элемент изображения.
 */
interface AnswerComponentProps {
  element: AnswerElement;
}

/**
 * Компонент для отображения настройки ответа.
 */
const AnswerComponent: React.FC<AnswerComponentProps> = ({ element }) => (
  <span>
    <button className="px-2 py-1 ml-2 mb-2 border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950">
      Настройка ответа
    </button>
    <br />
  </span>
);

export default AnswerComponent;
