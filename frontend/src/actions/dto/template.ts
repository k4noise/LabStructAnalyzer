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
   * Уникальный идентификатор элемента.
   * @type {string}
   */
  id: string;
  /**
   * Данные, содержащиеся в элементе. Может быть строкой, массивом элементов или массивом массивов элементов.
   * @type {string | TemplateElement[] | TemplateElement[][]}
   */
  data: string | TemplateElement[] | TemplateElement[][];
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
 * @extends {TemplateElement}
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
 * @extends {TemplateElement}
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
 * @extends {TemplateElement}
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
 * @extends {TextElement}
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
 * @interface AnswerElement
 */
export interface AnswerElement {
  /**
   * Тип элемента - "answer".
   * @type {"answer"}
   */
  type: "answer";
  /**
   * Уникальный идентификатор элемента.
   * @type {string}
   */
  id: string;
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
 * Интерфейс, представляющий элемент ячейки таблицы.
 * @interface CellElement
 * @extends {TemplateElement}
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
 * @extends {TemplateElement}
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
   * @type {CellElement[][]}
   */
  data: CellElement[][];
}

/**
 * Интерфейс, представляющий составной элемент.
 * @interface CompositeElement
 * @extends {TemplateElement}
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
