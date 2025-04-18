import { createContext } from "react";
import { AnswerElement } from "../model/templateElement";
import { AnswerModel } from "../model/answer";
import WeightToScoreManager from "../manager/WeightToScoreManager";

/**
 * Интерфейс для контекста ответов.
 * @interface
 */
interface AnswerContextProps {
  /**
   * Коллбек, вызываемый при выборе ответа для редактирования.
   * @param {AnswerElement} element - элемент ответа, который был выбран для редактирования его свойств
   */
  handleSelectAnswerForEdit?: (event, element: AnswerElement) => void;
  editAnswerPropsMode?: boolean;
  answers?: {
    [id: string]: AnswerModel;
  };
  weightToScoreManager?: WeightToScoreManager;
  updateAnswer?: (answer: AnswerModel) => void;
  editable?: boolean;
  graderView?: boolean;
}

/**
 * Контекст, предоставляющий возможности выбора ответа для редактирования.
 * По умолчанию - undefined, чтобы отличать неиницилизированный контекст.
 * @type {React.Context<AnswerContextProps | undefined>}
 */
const AnswerContext = createContext<AnswerContextProps | undefined>(undefined);

export default AnswerContext;
export type { AnswerContextProps };
