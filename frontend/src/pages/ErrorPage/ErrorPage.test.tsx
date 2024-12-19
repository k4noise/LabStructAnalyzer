import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { MemoryRouter, useNavigate, useSearchParams } from "react-router";
import ErrorPage from "./ErrorPage";

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: vi.fn(),
    useSearchParams: vi.fn(),
  };
});

describe("ErrorPage Component", () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Проверяет, что компонент отображает код ошибки и сообщение по умолчанию,
   * когда нет параметров в строке запроса.
   */
  it("renders default error code and message when no search params", () => {
    vi.mocked(useSearchParams).mockReturnValue([
      new URLSearchParams(),
      vi.fn(),
    ]);

    render(
      <MemoryRouter>
        <ErrorPage />
      </MemoryRouter>
    );

    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Не найдено")).toBeInTheDocument();
  });

  /**
   * Проверяет, что компонент отображает пользовательский код ошибки и описание,
   * переданные через параметры строки запроса.
   */
  it("renders custom error code and description from search params", () => {
    vi.mocked(useSearchParams).mockReturnValue([
      new URLSearchParams({
        code: "500",
        description: "Internal Server Error",
      }),
      vi.fn(),
    ]);

    render(
      <MemoryRouter>
        <ErrorPage />
      </MemoryRouter>
    );

    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("Internal Server Error")).toBeInTheDocument();
  });

  /**
   * Проверяет, что компонент корректно парсит JSON-описание из параметров строки запроса.
   */
  it("parses JSON description from search params", () => {
    const jsonDescription = `${JSON.stringify({ error: "invalid request" })}`;
    vi.mocked(useSearchParams).mockReturnValue([
      new URLSearchParams({ code: "400", description: jsonDescription }),
      vi.fn(),
    ]);

    render(
      <MemoryRouter>
        <ErrorPage />
      </MemoryRouter>
    );

    expect(screen.getByText("400")).toBeInTheDocument();
    expect(screen.getByText('{"error":"invalid request"}')).toBeInTheDocument();
  });

  /**
   * Проверяет, что компонент обрабатывает некорректный JSON-описание грациозно,
   * отображая код ошибки и сообщение по умолчанию.
   */
  it("handles invalid JSON gracefully", () => {
    const invalidJsonDescription = '"{\\"error\\":\\"Invalid Request"';
    vi.mocked(useSearchParams).mockReturnValue([
      new URLSearchParams({ description: invalidJsonDescription }),
      vi.fn(),
    ]);

    render(
      <MemoryRouter>
        <ErrorPage />
      </MemoryRouter>
    );

    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Не найдено")).toBeInTheDocument();
  });

  /**
   * Проверяет, что компонент возвращает на предыдущую страницу при нажатии на кнопку "Назад".
   */
  it('navigates back when "Назад" button is clicked', () => {
    vi.mocked(useSearchParams).mockReturnValue([
      new URLSearchParams(),
      vi.fn(),
    ]);

    render(
      <MemoryRouter>
        <ErrorPage />
      </MemoryRouter>
    );

    const backButton = screen.getByText("Назад");
    fireEvent.click(backButton);

    expect(mockNavigate).toHaveBeenCalledWith(-1, { replace: true });
  });
});
