import { describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Templates from "./Templates";
import { useLoaderData, useNavigate } from "react-router";
import { sendTemplate } from "../../api/sendTemplate";
import React from "react";

// Мокаем зависимости
vi.mock("react-router", () => ({
  useLoaderData: vi.fn(),
  useNavigate: vi.fn(),
}));

vi.mock("../../api/sendTemplate", () => ({
  sendTemplate: vi.fn(),
}));

/**
 * Набор тестов для компонента Templates
 */
describe("Templates Component", () => {
  /**
   * Подготовка общих моков перед каждым тестом
   */
  beforeEach(() => {
    vi.mocked(useLoaderData).mockReturnValue({ name: "Тестовый курс" });
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
  });

  /**
   * Очистка всех моков после каждого теста
   */
  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Тест на корректное отображение названия курса
   */
  it("отображает название курса", () => {
    render(<Templates />);
    expect(
      screen.getByText(/Отчеты лабораторных работ курса Тестовый курс/i)
    ).toBeInTheDocument();
  });

  /**
   * Тест на открытие/закрытие модального окна
   */
  it("открывает и закрывает модальное окно", async () => {
    render(<Templates />);

    expect(screen.queryByText("Шаблон для импорта")).not.toBeInTheDocument();

    const openButton = screen.getByText("+ Добавить новый шаблон");
    await userEvent.click(openButton);

    expect(screen.getByText("Шаблон для импорта")).toBeInTheDocument();
  });

  /**
   * Тест на загрузку шаблона
   */
  it("обрабатывает загрузку шаблона", async () => {
    const navigateMock = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(navigateMock);

    vi.mocked(sendTemplate).mockResolvedValue({
      data: { template_id: "123" },
      description: null,
    });

    render(<Templates />);

    const openButton = screen.getByText("+ Добавить новый шаблон");
    await userEvent.click(openButton);

    const file = new File([Buffer.from("Hello World!")], "test.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    const fileInput = screen.getByTestId("template");
    await userEvent.upload(fileInput, file);

    const submitButton = screen.getByText("Загрузить");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/template/123");
    });
  });

  /**
   * Тест на обработку ошибки при загрузке шаблона
   */
  it("отображает ошибку при неудачной загрузке", async () => {
    const errorMessage = "Ошибка загрузки";

    vi.mocked(sendTemplate).mockResolvedValue({
      data: null,
      description: errorMessage,
    });

    render(<Templates />);

    await userEvent.click(screen.getByText("+ Добавить новый шаблон"));

    const file = new File(["test content"], "test.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    const fileInput = screen.getByTestId("template");
    const form = fileInput.closest("form");

    await userEvent.upload(fileInput, file);

    await act(async () => {
      fireEvent.submit(form!);
    });

    await waitFor(
      () => {
        const errorElement = screen.getByText((content) =>
          content.includes(errorMessage)
        );
        expect(errorElement).toBeInTheDocument();
      },
      {
        timeout: 1000,
      }
    );

    expect(sendTemplate).toHaveBeenCalled();
    expect(screen.queryByText("Загрузка...")).not.toBeInTheDocument();
  });
});
