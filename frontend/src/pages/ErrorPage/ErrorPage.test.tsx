import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { useRouteError, MemoryRouter } from "react-router";
import ErrorPage from "./ErrorPage";
import { extractMessage } from "../../utils/sendRequest";
import { AxiosError } from "axios";
import React from "react";

/**
 * Мокирование хука useRouteError из react-router.
 */
vi.mock("react-router", async () => ({
  ...(await vi.importActual("react-router")),
  useRouteError: vi.fn(),
}));

/**
 * Мокирование функции extractMessage из utils/sendRequest.
 */
vi.mock("../../utils/sendRequest", async () => ({
  ...(await vi.importActual("../../utils/sendRequest")),
  extractMessage: vi.fn(),
}));

/**
 * Тесты для компонента ErrorPage.
 */
describe("ErrorPage", () => {
  /**
   * Экземпляр ошибки для тестирования.
   */
  const mockError = new Error("Something went wrong");

  /**
   * Экземпляр ошибки Axios для тестирования.
   */
  const mockAxiosError = new AxiosError(
    "Network error",
    "ECONNABORTED",
    undefined,
    undefined,
    {
      status: 500,
      data: { message: "Internal Server Error" },
    }
  );

  /**
   * Переустановка всех моков перед каждым тестом.
   */
  beforeEach(() => {
    vi.resetAllMocks();
  });

  /**
   * Функция для рендеринга ErrorPage с заданной ошибкой.
   * @param {Error | AxiosError | null} error - Ошибка для рендеринга.
   */
  const renderWithError = (error: Error | AxiosError | null) => {
    (useRouteError as vi.Mock).mockReturnValue(error);
    render(
      <MemoryRouter>
        <ErrorPage />
      </MemoryRouter>
    );
  };

  /**
   * Тест: отображение 404 при отсутствии ошибки.
   */
  it("should display 404 when no error is provided", () => {
    renderWithError(null);
    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Не найдено")).toBeInTheDocument();
  });

  /**
   * Тест: отображение ошибки Axios со статусом и сообщением.
   */
  it("should display Axios error with status and message", () => {
    (extractMessage as vi.Mock).mockReturnValue("Internal Server Error");
    renderWithError(mockAxiosError);
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("Internal Server Error")).toBeInTheDocument();
  });

  /**
   * Тест: отображение сообщения ошибки по умолчанию.
   */
  it("should display default error message", () => {
    renderWithError(mockError);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  /**
   * Тест: обработка JSON-сообщения из ошибки Axios.
   */
  it("should handle JSON message from Axios error", () => {
    (extractMessage as vi.Mock).mockReturnValue({
      test: 123,
    });
    renderWithError(mockAxiosError);
    expect(screen.getByText("500")).toBeInTheDocument();

    const preElement = screen.getByTestId("json");
    expect(preElement.textContent).toBe(`{
  "test": 123
}`);
  });
});
