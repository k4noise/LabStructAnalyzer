export interface AnswerEdit {
  customId: string;
  /**
   * Вес ответа - number
   * @type {number}
   */
  weight: number;
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
  pre_grade?: {
    score: number;
    comment?: string;
  }
  given_score?: number;
}

export interface AnswerDataModel {
  text?: string;
}
