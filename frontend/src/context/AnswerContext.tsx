import { createContext } from "react";
import { AnswerElement } from "../model/template";

/**
 * Интерфейс для контекста ответов.
 * @interface
 */
interface AnswerContextProps {
  /**
   * Коллбек, вызываемый при выборе ответа для редактирования.
   * @param {AnswerElement} element - элемент ответа, который был выбран для редактирования его свойств
   */
  handleSelectAnswerForEdit: (element: AnswerElement) => void;
}

/**
 * Контекст, предоставляющий возможности выбора ответа для редактирования.
 * По умолчанию - undefined, чтобы отличать неиницилизированный контекст.
 * @type {React.Context<AnswerContextProps | undefined>}
 */
const AnswerContext = createContext<AnswerContextProps | undefined>(undefined);

export default AnswerContext;
