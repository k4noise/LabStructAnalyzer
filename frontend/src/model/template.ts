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

export interface TemplateElementModel {
  id: string;
  type: string;
  properties: TemplateElement;
}

/**
 * Интерфейс, представляющий базовый элемент шаблона.
 * @interface TemplateElement
 */
export interface TemplateElement {
  /**
   * Тип элемента. Например, "text", "image", "header", "table" и т.д.
   * @type {string}
   */
  type: string;
  /**
   * Данные, содержащиеся в элементе. Может быть строкой или массивом элементов .
   * @type {string | TemplateElement[]}
   */
  data: string | TemplateElement[];
  /**
   * Тип содержимого элемента. Например, "text", "image", "table" и т.д.
   * @type {string}
   */
  contentType: string;
  /**
   * Режим отображения элемента.
   * @type {"always" | "prefer"}
   * @optional
   */
  displayMode?: "always" | "prefer";
  /**
   * Уровень вложенности элемента.
   * @type {number}
   * @optional
   */
  nestingLevel?: number;
  /**
   * Текст маркера нумерованного списка.
   * @type {string}
   * @optional
   */
  numberingBulletText?: string;
}

/**
 * Интерфейс, представляющий текстовый элемент.
 * @interface TextElement
 */
export interface TextElement extends TemplateElement {
  /**
   * Тип элемента - "text".
   * @type {"text"}
   */
  type: "text";
  /**
   * Текстовые данные.
   * @type {string}
   */
  data: string;
  /**
   * Тип содержимого - "text".
   * @type {"text"}
   */
  contentType: "text";
}

/**
 * Интерфейс, представляющий элемент изображения.
 * @interface ImageElement
 */
export interface ImageElement extends TemplateElement {
  /**
   * Тип элемента - "image".
   * @type {"image"}
   */
  type: "image";
  /**
   * URL или base64 представление изображения.
   * @type {string}
   */
  data: string;
  /**
   * Тип содержимого - "image".
   * @type {"image"}
   */
  contentType: "image";
}

/**
 * Интерфейс, представляющий элемент заголовка.
 * @interface HeaderElement
 */
export interface HeaderElement extends TemplateElement {
  /**
   * Тип элемента - "header".
   * @type {"header"}
   */
  type: "header";
  /**
   * Текст заголовка.
   * @type {string}
   */
  data: string;
  /**
   * Тип содержимого - "text".
   * @type {"text"}
   */
  contentType: "text";
  /**
   * Уровень заголовка (например, 1 для <h1>, 2 для <h2> и т.д.).
   * @type {number}
   */
  headerLevel: number;
}

/**
 * Интерфейс, представляющий элемент вопроса.
 * @interface QuestionElement
 */
export interface QuestionElement extends TextElement {
  /**
   * Тип элемента - "text".
   * @type {"text"}
   */
  type: "text";
  /**
   * Текст вопроса.
   * @type {string}
   */
  data: string;
  /**
   * Тип содержимого - "text".
   * @type {"text"}
   */
  contentType: "text";
  /**
   * Режим отображения - "always".
   * @type {"always"}
   */
  displayMode: "always";
}

/**
 * Интерфейс, представляющий элемент ответа.
 * @interface AnswerElement {
 */
interface AnswerElement {
  /**
   * Тип элемента - "answer".
   * @type {"answer"}
   */
  type: "answer";
  /**
   * Тип содержимого - "answer".
   * @type {"answer"}
   */
  contentType: "answer";
  /**
   * Уровень вложенности элемента.
   * @type {number}
   * @optional
   */
  nestingLevel?: number;
}

/**
 * Интерфейс, представляющий элемент строки таблицы.
 * @interface RowElement
 */
export interface RowElement extends TemplateElement {
  /**
   * Тип элемента - "row".
   * @type {"row"}
   */
  type: "row";
  /**
   * Содержимое строки (массив ячеек).
   * @type {CellElement[]}
   */
  data: CellElement[];
}

/**
 * Интерфейс, представляющий элемент ячейки таблицы.
 * @interface CellElement
 */
export interface CellElement extends TemplateElement {
  /**
   * Тип элемента - "cell".
   * @type {"cell"}
   */
  type: "cell";
  /**
   * Содержимое ячейки (массив элементов).
   * @type {TemplateElement[]}
   */
  data: TemplateElement[];
  /**
   * Объединена ли ячейка с соседними.
   * @type {boolean}
   * @optional
   */
  merged?: boolean;
  /**
   * Количество объединенных строк.
   * @type {number}
   * @optional
   */
  rows?: number;
  /**
   * Количество объединенных столбцов.
   * @type {number}
   * @optional
   */
  cols?: number;
}

/**
 * Интерфейс, представляющий элемент таблицы.
 * @interface TableElement
 */
export interface TableElement extends TemplateElement {
  /**
   * Тип элемента - "table".
   * @type {"table"}
   */
  type: "table";
  /**
   * Тип содержимого - "table".
   * @type {"table"}
   */
  contentType: "table";
  /**
   * Данные таблицы (двумерный массив ячеек).
   * @type {RowElement[]}
   */
  data: RowElement[];
}

/**
 * Интерфейс, представляющий составной элемент.
 * @interface CompositeElement
 */
export interface CompositeElement extends TemplateElement {
  /**
   * Тип элемента.
   * @type {string}
   */
  type: string;
  /**
   * Дочерние элементы.
   * @type {TemplateElement[]}
   */
  data: TemplateElement[];
}
