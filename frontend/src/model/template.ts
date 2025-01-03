import { TemplateElementModel } from "./templateElement";

/**
 * Интерфейс, представляющий элемент шаблона.
 * @interface Template
 */
export interface TemplateModel {
  template_id: string;
  name: string;
  is_draft: boolean;
  max_score: number;
  elements: TemplateElementModel[];
}

export interface UpdateTemplateModel {
  name: string;
  is_draft: boolean;
  max_score: number;
  deleted_elements?: Partial<TemplateElementModel>[];
  updated_elements?: Partial<TemplateElementModel>[];
}
