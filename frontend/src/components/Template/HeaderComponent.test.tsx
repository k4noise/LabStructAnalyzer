import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import HeaderComponent from "./HeaderComponent";
import { describe, it, expect } from "vitest";
import { HeaderElement } from "../../actions/dto/template";

vi.mock("../../utils/templateStyle", () => ({
  getMarginLeftStyle: (nestingLevel: number) => `ml-${nestingLevel}`,
}));

describe("HeaderComponent", () => {
  /**
   * Проверяет, что компонент отображает правильный уровень заголовка (h1).
   * Ожидается, что заголовок будет отображаться с текстом "Header 1" и классом стиля "ml-0".
   */
  it("renders the correct header level (h1)", () => {
    const element: HeaderElement = {
      headerLevel: 1,
      nestingLevel: 0,
      data: "Header 1",
      numberingBulletText: "",
    };

    render(<HeaderComponent element={element} />);

    const headerElement = screen.getByRole("heading", { level: 1 });
    expect(headerElement).toBeInTheDocument();
    expect(headerElement).toHaveTextContent("Header 1");
    expect(headerElement).toHaveClass("ml-0");
  });

  /**
   * Проверяет, что компонент отображает правильный уровень заголовка (h3) при отсутствии значения headerLevel.
   * Ожидается, что заголовок будет отображаться с текстом "Default Header" и классом стиля "ml-2".
   */
  it("renders the correct header level (h3) when headerLevel is undefined", () => {
    const element: HeaderElement = {
      headerLevel: undefined,
      nestingLevel: 2,
      data: "Default Header",
      numberingBulletText: "",
    };

    render(<HeaderComponent element={element} />);

    const headerElement = screen.getByRole("heading", { level: 3 });
    expect(headerElement).toBeInTheDocument();
    expect(headerElement).toHaveTextContent("Default Header");
    expect(headerElement).toHaveClass("ml-2");
  });

  /**
   * Проверяет, что компонент отображает numberingBulletText вместе с текстом заголовка.
   * Ожидается, что заголовок будет отображаться с текстом "1.1 Section Title" и классом стиля "ml-1".
   */
  it("renders numberingBulletText with data", () => {
    const element: HeaderElement = {
      headerLevel: 2,
      nestingLevel: 1,
      data: "Section Title",
      numberingBulletText: "1.1",
    };

    render(<HeaderComponent element={element} />);

    const headerElement = screen.getByRole("heading", { level: 2 });
    expect(headerElement).toBeInTheDocument();
    expect(headerElement).toHaveTextContent("1.1 Section Title");
    expect(headerElement).toHaveClass("ml-1");
  });

  /**
   * Проверяет, что компонент отображает заголовок без numberingBulletText.
   * Ожидается, что заголовок будет отображаться с текстом "No Numbering" и классом стиля "ml-3".
   */
  it("renders without numberingBulletText", () => {
    const element: HeaderElement = {
      headerLevel: 4,
      nestingLevel: 3,
      data: "No Numbering",
      numberingBulletText: "",
    };

    render(<HeaderComponent element={element} />);

    const headerElement = screen.getByRole("heading", { level: 4 });
    expect(headerElement).toBeInTheDocument();
    expect(headerElement).toHaveTextContent("No Numbering");
    expect(headerElement).toHaveClass("ml-3");
  });
});
