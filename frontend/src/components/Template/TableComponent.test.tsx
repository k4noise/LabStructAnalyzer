import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { describe, it, expect, vi } from "vitest";
import TableComponent from "./TableComponent";
import { TableElement } from "../../actions/dto/template";

vi.mock("../../utils/templateStyle", () => ({
  getMarginLeftStyle: (nestingLevel: number) => `ml-${nestingLevel}`,
}));

vi.mock("../../pages/Template/Template", () => ({
  renderElement: vi.fn((element) => <span>{element.data}</span>),
}));

describe("TableComponent", () => {
  /**
   * Проверяет, что компонент корректно отображает таблицу с базовыми данными.
   */
  it("render simple table", () => {
    const tableElement: TableElement = {
      type: "table",
      nestingLevel: 1,
      data: [
        [
          { data: [{ type: "text", data: "Cell 1-1" }] },
          { data: [{ type: "text", data: "Cell 1-2" }] },
        ],
        [
          { data: [{ type: "text", data: "Cell 2-1" }] },
          { data: [{ type: "text", data: "Cell 2-2" }] },
        ],
      ],
    };

    render(<TableComponent element={tableElement} />);

    expect(screen.getByText("Cell 1-1")).toBeInTheDocument();
    expect(screen.getByText("Cell 1-2")).toBeInTheDocument();
    expect(screen.getByText("Cell 2-1")).toBeInTheDocument();
    expect(screen.getByText("Cell 2-2")).toBeInTheDocument();
    expect(screen.getByRole("table")).toHaveClass("ml-1");
  });

  /**
   * Проверяет, что компонент корректно обрабатывает объединенные ячейки.
   */
  it("render with merged col", () => {
    const tableElement: TableElement = {
      type: "table",
      nestingLevel: 2,
      data: [
        [{ data: [{ type: "text", data: "Cell 1-1" }], merged: true, cols: 2 }],
        [
          { data: [{ type: "text", data: "Cell 2-1" }] },
          { data: [{ type: "text", data: "Cell 2-2" }] },
        ],
      ],
    };

    render(<TableComponent element={tableElement} />);

    const cell11 = screen.getByText("Cell 1-1");
    expect(cell11).toBeInTheDocument();
    expect(cell11).toHaveAttribute("colSpan", "2");

    expect(screen.getByText("Cell 2-1")).toBeInTheDocument();
    expect(screen.getByText("Cell 2-2")).toBeInTheDocument();
    expect(screen.getByRole("table")).toHaveClass("ml-2");
  });

  /**
   * Проверяет, что компонент корректно отображает вложенные элементы в ячейках таблицы.
   */
  it("correct nesting items render", () => {
    const tableElement: TableElement = {
      type: "table",
      nestingLevel: 0,
      data: [
        [
          {
            data: [
              { type: "text", data: "Nested Text 1" },
              { type: "text", data: "Nested Text 2" },
            ],
          },
        ],
      ],
    };

    render(<TableComponent element={tableElement} />);

    expect(screen.getByText("Nested Text 1")).toBeInTheDocument();
    expect(screen.getByText("Nested Text 2")).toBeInTheDocument();
  });

  /**
   * Проверяет, что компонент корректно отображает пустую таблицу.
   */
  it("empty table", () => {
    const tableElement: TableElement = {
      type: "table",
      nestingLevel: 1,
      data: [],
    };

    render(<TableComponent element={tableElement} />);

    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();
    expect(table).toHaveClass("ml-1");
    const tbody = table.querySelector("tbody");
    expect(tbody).toBeInTheDocument();
    expect(tbody).toBeEmptyDOMElement();
  });
});
