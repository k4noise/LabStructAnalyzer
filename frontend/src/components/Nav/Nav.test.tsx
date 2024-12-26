import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { useLoaderData } from "react-router";
import Nav from "./Nav";
import React from "react";

/**
 * Мокаем хук useLoaderData из react-router
 */
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useLoaderData: vi.fn(),
  };
});

/**
 * Тесты для Nav компонента
 */
describe("Nav Component", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Проверяет отображение аватара пользователя и имени студента
   */
  it("Displays the user avatar and student name", () => {
    (useLoaderData as vi.Mock).mockReturnValue({
      avatarUrl: "https://example.com/avatar.jpg",
      role: "student",
      name: "Иван",
      surname: "Иванов",
      fullName: "Иван Иванов",
    });

    render(<Nav />);

    const avatarImage = screen.getByAltText("avatar");
    expect(avatarImage).toBeInTheDocument();
    expect(avatarImage).toHaveAttribute(
      "src",
      "https://example.com/avatar.jpg"
    );

    expect(screen.getByText("Иван Иванов")).toBeInTheDocument();
  });

  /**
   * Проверяет отображение полного имени пользователя при роли, отличной от студента
   */
  it("Displays the full user name for a role other than student", () => {
    (useLoaderData as vi.Mock).mockReturnValue({
      avatarUrl: "https://example.com/avatar.jpg",
      role: "admin",
      fullName: "Админ Иванов",
    });

    render(<Nav />);

    const avatarImage = screen.getByAltText("avatar");
    expect(avatarImage).toBeInTheDocument();
    expect(avatarImage).toHaveAttribute(
      "src",
      "https://example.com/avatar.jpg"
    );

    expect(screen.getByText("Админ Иванов")).toBeInTheDocument();
  });

  /**
   * Проверяет отсутствие аватара, если avatarUrl не передан
   */
  it("Does not display avatar if avatarUrl is missing", () => {
    (useLoaderData as vi.Mock).mockReturnValue({
      role: "student",
      name: "Иван",
      surname: "Иванов",
      fullName: "Иван Иванов",
    });

    render(<Nav />);

    const avatarImage = screen.queryByAltText("avatar");
    expect(avatarImage).not.toBeInTheDocument();

    expect(screen.getByText("Иван Иванов")).toBeInTheDocument();
  });

  /**
   * Проверяет отсутствие имени, если fullName не передан
   */
  it("Does not display name if fullName is missing", () => {
    (useLoaderData as vi.Mock).mockReturnValue({
      avatarUrl: "https://example.com/avatar.jpg",
      role: "student",
    });

    render(<Nav />);

    const avatarImage = screen.getByAltText("avatar");
    expect(avatarImage).toBeInTheDocument();
    expect(avatarImage).toHaveAttribute(
      "src",
      "https://example.com/avatar.jpg"
    );

    const nameElement = screen.queryByText(/Иван Иванов/);
    expect(nameElement).not.toBeInTheDocument();
  });
});
