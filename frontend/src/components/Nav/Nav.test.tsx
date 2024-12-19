import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { useNavigate } from "react-router";
import { getUser } from "../../actions/getUser";
import Nav from "./Nav";

vi.mock("react-router", () => ({
  useNavigate: vi.fn(),
}));

vi.mock("../../actions/getUser", () => ({
  getUser: vi.fn(),
}));

describe("Nav Component", () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    (useNavigate as vi.Mock).mockReturnValue(mockNavigate);
  });

  /**
   * Тестирует корректный рендер компонента при успешном получении данных пользователя.
   */
  it("renders correctly when user data is fetched", async () => {
    const mockUserData = {
      data: {
        avatarUrl: "https://example.com/avatar.jpg",
        fullName: "John Doe",
        name: "John",
        surname: "Doe",
        role: ["student"],
      },
      error: null,
      description: null,
    };

    (getUser as vi.Mock).mockResolvedValue(mockUserData);

    render(<Nav />);

    await waitFor(() => {
      expect(screen.getByAltText("avatar")).toBeInTheDocument();
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    expect(screen.getByAltText("avatar")).toHaveAttribute(
      "src",
      "https://example.com/avatar.jpg"
    );
  });

  /**
   * Тестирует навигацию на страницу ошибки при возникновении ошибки API.
   */
  it("navigates to error page on API error", async () => {
    const mockErrorResponse = {
      data: null,
      error: "403",
      description: "Forbidden",
    };

    (getUser as vi.Mock).mockResolvedValue(mockErrorResponse);

    render(<Nav />);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        "/error?code=403&description=Forbidden"
      );
    });
  });

  /**
   * Тестирует, что функция getUser не вызывается повторно, если данные пользователя уже установлены.
   */
  it("does not call getUser again if userData is already set", async () => {
    const mockUserData = {
      data: {
        avatarUrl: "https://example.com/avatar.jpg",
        fullName: "John Doe",
        name: "John",
        surname: "Doe",
        role: ["student"],
      },
      error: null,
      description: null,
    };

    (getUser as vi.Mock).mockResolvedValue(mockUserData);

    const { rerender } = render(<Nav />);

    await waitFor(() => {
      expect(screen.getByAltText("avatar")).toBeInTheDocument();
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    rerender(<Nav />);

    expect(getUser).toHaveBeenCalledTimes(1);
  });
});
