import { useContext } from "react";
import { AnswerElement } from "../../model/templateElement";
import AnswerContext from "../../context/AnswerContext";
import Button from "../Button/Button";

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
const AnswerComponent: React.FC<AnswerComponentProps> = ({ element }) => {
  const { handleSelectAnswerForEdit } = useContext(AnswerContext);
  return (
    <>
      <Button
        text="⚙️ Настройка ответа"
        classes="ml-2 mb-2"
        onClick={() => handleSelectAnswerForEdit(element)}
      />
      <br />
    </>
  );
};

export default AnswerComponent;
