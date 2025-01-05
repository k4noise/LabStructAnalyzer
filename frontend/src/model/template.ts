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
  teacher_interface: boolean;
  elements: TemplateElementModel[];
}

export interface UpdateTemplateModel {
  name: string;
  is_draft: boolean;
  max_score: number;
  deleted_elements?: Partial<TemplateElementModel>[];
  updated_elements?: Partial<TemplateElementModel>[];
}

export interface MinimalTemplateInfo {
  template_id: string;
  name: string;
}

export interface AllTemplatesInfo {
  teacher_interface: boolean;
  course_name: string;
  templates: MinimalTemplateInfo[];
  drafts?: MinimalTemplateInfo[];
}
