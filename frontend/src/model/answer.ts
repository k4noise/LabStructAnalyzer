export interface AnswerEdit {
  customId: string;
  /**
   * Вес ответа - number
   * @type {number}
   */
  weight: number;
  /**
   * Простой ответ - boolean
   * @type {boolean}
   */
  simple: boolean;
}

export interface AnswerModel {
  element_id: string;
  answer_id?: string;
  data?: {
    text?: string;
    image?: string;
  };
  score?: number;
}
