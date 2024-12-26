import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { renderElement } from "./Template";
import { TemplateElement } from "../../api/dto/template";
import React from "react";

vi.mock("../../components/Template/TextQuestionComponent", () => ({
  default: ({ element }: { element: TemplateElement }) => {
    return element.type === "question" ? (
      <div data-testid="text-question">{element.data}</div>
    ) : (
      <div data-testid="text">{element.data}</div>
    );
  },
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

/**
 * Тесты для функции renderElement.
 */
describe("renderElement function", () => {
  /**
   * Проверяет корректность рендеринга вложенных элементов.
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
   * Проверяет, что функция возвращает null для неизвестного типа элемента.
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
   * Проверяет обработку всех поддерживаемых типов элементов.
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
