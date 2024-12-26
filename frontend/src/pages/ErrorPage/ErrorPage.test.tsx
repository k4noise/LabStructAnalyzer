import { render, screen } from "@testing-library/react";
import { Mock, vi } from "vitest";
import { useRouteError } from "react-router";
import ErrorPage from "./ErrorPage";
import React from "react";

// Мок компонента BackButtonComponent
vi.mock("../../components/BackButtonComponent", () => {
  return {
    default: () => <button data-testid="back-button">Back</button>,
  };
});

// Мок useRouteError
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useRouteError: vi.fn(),
  };
});

/**
 * Набор тестов для компонента ErrorPage
 */
describe("ErrorPage Component", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Проверяет отображение страницы 404 при отсутствии ошибки
   */
  it("Displays default 404 when no error is present", () => {
    (useRouteError as Mock).mockReturnValue(undefined);

    render(<ErrorPage />);

    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Не найдено")).toBeInTheDocument();
    expect(screen.getByTestId("back-button")).toBeInTheDocument();
  });

  /**
   * Проверяет отображение пользовательской ошибки из JSON
   */
  it("Displays custom error from JSON", () => {
    const errorMock = {
      message: JSON.stringify({
        status: 500,
        message: "Внутренняя ошибка сервера",
      }),
    };

    (useRouteError as Mock).mockReturnValue(errorMock);

    render(<ErrorPage />);

    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("Внутренняя ошибка сервера")).toBeInTheDocument();
    expect(screen.getByTestId("back-button")).toBeInTheDocument();
  });

  /**
   * Проверяет отображение сообщения по умолчанию при пустом message
   */
  it("Shows default message when message is empty", () => {
    const errorMock = {
      message: JSON.stringify({ status: 500, message: "" }),
    };

    (useRouteError as Mock).mockReturnValue(errorMock);

    render(<ErrorPage />);

    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("Не найдено")).toBeInTheDocument();
    expect(screen.getByTestId("back-button")).toBeInTheDocument();
  });

  /**
   * Проверяет обработку некорректного JSON в ошибке
   */
  it("Handles invalid JSON in error", () => {
    const errorMock = {
      message: "Некорректный JSON",
    };

    (useRouteError as Mock).mockReturnValue(errorMock);

    render(<ErrorPage />);

    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Не найдено")).toBeInTheDocument();
    expect(screen.getByTestId("back-button")).toBeInTheDocument();
  });
});
