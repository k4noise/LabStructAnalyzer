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
   * Простой ответ - boolean
   * @type {boolean}
   */
  simple: boolean;
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
