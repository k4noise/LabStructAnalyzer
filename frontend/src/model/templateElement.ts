import { AnswerEdit } from "./answer";

export interface TemplateElementModel {
  element_id: string;
  element_type: string;
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
   * @type {string | TemplateElementModel[]}
   */
  data: string | TemplateElementModel[];
  /**
   * Тип содержимого элемента. Например, "text", "image", "table" и т.д.
   * Отсутствует только у составных элементов
   * @type {string}
   */
  contentType?: string;
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
}

/**
 * Интерфейс, представляющий текстовый элемент.
 * @interface TextElement
 */
export interface TextElement extends TemplateElementModel {
  element_type: "text";
  properties: TemplateElement & {
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
    /**
     * Текст маркера нумерованного списка.
     * @type {string}
     * @optional
     */
    numberingBulletText?: string;
  };
}

/**
 * Интерфейс, представляющий элемент изображения.
 * @interface ImageElement
 */
export interface ImageElement extends TemplateElementModel {
  element_type: "image";
  properties: TemplateElement & {
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
  };
}

/**
 * Интерфейс, представляющий элемент заголовка.
 * @interface HeaderElement
 */
export interface HeaderElement extends TemplateElementModel {
  element_type: "header";
  properties: TemplateElement & {
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
    /**
     * Текст маркера нумерованного списка.
     * @type {string}
     * @optional
     */
    numberingBulletText?: string;
  };
}

/**
 * Интерфейс, представляющий элемент вопроса.
 * @interface QuestionElement
 */
export interface QuestionElement extends TemplateElementModel {
  content_type: "question";
  properties: TemplateElement & {
    /**
     * Тип элемента - "text".
     * @type {"text"}
     */
    type: "text";
    /**
     * Элементы вопроса
     * @type {[TextElement, AnswerElement]}
     */
    data: [TextElement, AnswerElement];
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
  };
}

/**
 * Интерфейс, представляющий элемент ответа.
 * @interface AnswerElement {
 */
export interface AnswerElement extends TemplateElementModel {
  element_type: "answer";
  properties: TemplateElement &
    AnswerEdit & {
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
       * Тип данных - string.
       * @type {string}
       */
      data: string;
      /**
       * Находится в режиме редактирования
       * @type {boolean}
       */
      editNow: boolean;
    };
}

/**
 * Интерфейс, представляющий элемент строки таблицы.
 * @interface RowElement
 */
export interface RowElement extends TemplateElementModel {
  element_type: "row";
  properties: TemplateElement & {
    /**
     * Тип элемента - "row".
     * @type {"row"}
     */
    type: "row";
    /**
     * Тип содержимого - "row".
     * @type {"row"}
     */
    contentType: "row";
    /**
     * Содержимое строки (массив ячеек).
     * @type {CellElement[]}
     */
    data: CellElement[];
  };
}

/**
 * Интерфейс, представляющий элемент ячейки таблицы.
 * @interface CellElement
 */
export interface CellElement extends TemplateElementModel {
  element_type: "cell";
  properties: TemplateElement & {
    /**
     * Тип элемента - "cell".
     * @type {"cell"}
     */
    type: "cell";
    /**
     * Тип элемента - "cell".
     * @type {"cell"}
     */
    contentType: "cell";
    /**
     * Содержимое ячейки (массив элементов).
     * @type {TemplateElementModel[]}
     */
    data: TemplateElementModel[];
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
  };
}

/**
 * Интерфейс, представляющий элемент таблицы.
 * @interface TableElement
 */
export interface TableElement extends TemplateElementModel {
  element_type: "table";
  properties: TemplateElement & {
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
  };
}

/**
 * Интерфейс, представляющий составной элемент.
 * @interface CompositeElement
 */
export interface CompositeElement extends TemplateElementModel {
  properties: TemplateElement & {
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
  };
}
