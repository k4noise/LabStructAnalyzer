import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Template, { renderElement } from "./Template";
import { TemplateElement } from "../../actions/dto/template";

vi.mock("../../components/Template/TextQuestionComponent", () => ({
  default: ({ element }: { element: TemplateElement }) => {
    {
      return element.type == "question" ? (
        <div data-testid="text-question">{element.data}</div>
      ) : (
        <div data-testid="text">{element.data}</div>
      );
    }
  },
}));

vi.mock("useLoaderData", () => ({
  template_id: "123",
  name: "lol",
  is_draft: true,
  max_score: 20,
  elements: [],
}));

vi.mock("../../components/Template/ImageComponent", () => ({
  default: ({ element }: { element: TemplateElement }) => (
    <div data-testid="image">{element.data}</div>
  ),
}));

vi.mock("../../components/Template/HeaderComponent", () => ({
  default: ({ element }: { element: TemplateElement }) => (
    <div data-testid="header">{element.data}</div>
  ),
}));

vi.mock("../../components/Template/TableComponent", () => ({
  default: ({ element }: { element: TemplateElement }) => (
    <div data-testid="table">{element.data}</div>
  ),
}));

vi.mock("../../components/Template/AnswerComponent", () => ({
  default: () => <div data-testid="answer">Answer Component</div>,
}));

describe("Template Component", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  /**
   * Тестирование отображения элементов шаблона из локального хранилища.
   */
  it("renders template elements from localStorage", () => {
    const mockData = [
      { id: "1", type: "text", data: "Text data" },
      { id: "2", type: "header", data: "Header data" },
    ];

    render(<Template />);

    expect(screen.getByTestId("text")).toBeInTheDocument();
    expect(screen.getByTestId("header")).toBeInTheDocument();
  });

  /**
   * Тестирование отображения компонента ответа для вопроса.
   */
  it("renders answer component for question type", () => {
    const mockData = [{ id: "1", type: "question", data: "Question data" }];

    render(<Template />);

    expect(screen.getByTestId("text-question")).toBeInTheDocument();
    expect(screen.getByTestId("answer")).toBeInTheDocument();
  });
});

/**
 * Описание тестов для функции renderElement.
 */
describe("renderElement function", () => {
  /**
   * Тестирование отображения вложенных элементов.
   */
  it("renders nested elements correctly", () => {
    const nestedElement = {
      type: "container",
      data: [
        { type: "text", data: "Nested Text", id: "1" },
        { type: "header", data: "Nested Header", id: "2" },
      ],
      nestingLevel: 2,
    };

    render(<div>{renderElement(nestedElement)}</div>);

    expect(screen.getByTestId("text")).toBeInTheDocument();
    expect(screen.getByTestId("header")).toBeInTheDocument();
  });

  /**
   * Тестирование возвращения null для неизвестного типа элемента.
   */
  it("returns null for unknown element type", () => {
    const unknownElement = {
      type: "unknown",
      data: "Unknown data",
      id: "1",
    };

    const { container } = render(<div>{renderElement(unknownElement)}</div>);

    expect(container.firstChild?.firstChild).toBeNull();
  });

  /**
   * Тестирование обработки всех поддерживаемых типов элементов.
   */
  it("handles all supported element types", () => {
    const elements = [
      { type: "text", data: "Text data", id: "1" },
      { type: "image", data: "Image data", id: "2" },
      { type: "header", data: "Header data", id: "3" },
      { type: "question", data: "Question data", id: "4" },
      { type: "table", data: "Table data", id: "5" },
    ];

    elements.forEach((element) => {
      render(<div>{renderElement(element)}</div>);
      expect(
        screen.getByTestId(
          element.type === "question" ? "text-question" : element.type
        )
      ).toBeInTheDocument();
    });
  });
});
