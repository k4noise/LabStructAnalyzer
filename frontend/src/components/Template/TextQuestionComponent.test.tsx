import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { describe, it, expect, vi } from "vitest";
import TextQuestionComponent from "./TextQuestionComponent";
import { TextElement, QuestionElement } from "../../actions/dto/template";
import React from "react";


vi.mock("../../utils/templateStyle", () => ({
  getMarginLeftStyle: (nestingLevel: number) => `ml-${nestingLevel}`,
}));

describe("TextQuestionComponent", () => {
  /**
   * Проверяет, что компонент корректно отображает текстовый элемент с дефолтными стилями.
   * Ожидается, что текст будет отображаться с классом стиля "ml-1" и без стилей курсива.
   */
  it("renders text element correctly with default styles", () => {
    const textElement: TextElement = {
      type: "text",
      nestingLevel: 1,
      data: "This is a text element",
      numberingBulletText: "",
    };

    render(<TextQuestionComponent element={textElement} />);

    const paragraph = screen.getByText("This is a text element");

    expect(paragraph).toBeInTheDocument();
    expect(paragraph).toHaveClass("ml-1");
    expect(paragraph).not.toHaveClass("italic");
  });

  /**
   * Проверяет, что компонент отображает вопросительный элемент с курсивными стилями.
   * Ожидается, что текст будет отображаться с классами стилей "italic inline-block my-3 ml-2".
   */
  it("renders question element with italic styles", () => {
    const questionElement: QuestionElement = {
      type: "question",
      nestingLevel: 2,
      data: "Is this a question?",
      numberingBulletText: "",
    };

    render(<TextQuestionComponent element={questionElement} />);

    const paragraph = screen.getByText("Is this a question?");

    expect(paragraph).toBeInTheDocument();
    expect(paragraph).toHaveClass("italic inline-block my-3 ml-2");
  });

  /**
   * Проверяет, что компонент отображает numberingBulletText, если он предоставлен.
   * Ожидается, что текст будет предварен номером "1.1".
   */
  it("renders numberingBulletText when provided", () => {
    const textElementWithNumbering: TextElement = {
      type: "text",
      nestingLevel: 0,
      data: "Numbered text",
      numberingBulletText: "1.1",
    };

    render(<TextQuestionComponent element={textElementWithNumbering} />);

    const numberingText = screen.getByText("1.1", { exact: false });
    expect(numberingText).toBeInTheDocument();
    expect(screen.getByText("Numbered text")).toBeInTheDocument();
  });

  /**
   * Проверяет, что компонент применяет стиль отступа слева (margin-left) на основе уровня вложенности.
   * Ожидается, что текст будет иметь класс стиля "ml-3".
   */
  it("applies margin-left style based on nestingLevel", () => {
    const textElement: TextElement = {
      type: "text",
      nestingLevel: 3,
      data: "Text with nesting level",
      numberingBulletText: "",
    };

    render(<TextQuestionComponent element={textElement} />);

    const paragraph = screen.getByText("Text with nesting level");

    expect(paragraph).toHaveClass("ml-3");
  });
});
