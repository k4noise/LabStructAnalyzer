export interface TemplateElement {
  type: string;
  id: string;
  data: string | TemplateElement[] | TemplateElement[][];
  contentType: string;
  displayMode?: "always" | "prefer";
  nestingLevel?: number;
  numberingBulletText?: string;
}

export interface TextElement extends TemplateElement {
  type: "text";
  data: string;
  contentType: "text";
}

export interface ImageElement extends TemplateElement {
  type: "image";
  data: string;
  contentType: "image";
}

export interface HeaderElement extends TemplateElement {
  type: "header";
  data: string;
  contentType: "text";
  headerLevel: number;
}

export interface QuestionElement extends TextElement {
  type: "text";
  data: string;
  contentType: "text";
  displayMode: "always";
}

export interface AnswerElement {
  type: "answer";
  id: string;
  contentType: "answer";
  nestingLevel?: number;
}


export interface CellElement extends TemplateElement {
  type: "cell";
  data: TemplateElement[];
  merged?: boolean;
  rows?: number;
  cols?: number;
}

export interface TableElement extends TemplateElement {
  type: "table";
  contentType: "table",
  data: CellElement[][];
}


export interface CompositeElement extends TemplateElement {
  type: string;
  data: TemplateElement[];
}