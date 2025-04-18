export interface AnswerEdit {
  customId: string;
  /**
   * Вес ответа - number
   * @type {number}
   */
  weight: number;
  /**
   * Тип ответа
   */
  answerType: "simple" | "param" | "arg";
  /**
   * Эталонный ответ преподавателя
   * @type {boolean}
   */
  refAnswer: string;
}

export interface AnswerModel {
  element_id: string;
  answer_id?: string;
  data?: AnswerDataModel;
  score?: number;
  given_score?: number;
}

export interface AnswerDataModel {
  text?: string;
}
