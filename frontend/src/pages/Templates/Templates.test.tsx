import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Templates from "./Templates";
import { useNavigate } from "react-router";
import * as sendTemplateModule from "../../actions/sendTemplate";
import * as getCourseNameModule from "../../actions/getCourseName";
import userEvent from "@testing-library/user-event";

vi.mock("react-router", () => ({
  useNavigate: vi.fn(),
}));

vi.mock("../../actions/sendTemplate", () => ({
  sendTemplate: vi.fn(),
}));

vi.mock("../../actions/getCourseName", () => ({
  getCourseName: vi.fn(),
}));

describe("Templates component", () => {
  const mockedNavigate = vi.fn();
  beforeEach(() => {
    vi.clearAllMocks();
    (useNavigate as ReturnType<typeof vi.fn>).mockReturnValue(mockedNavigate);
  });

  /**
   * Тест проверяет корректность рендеринга компонента
   * Ожидается успешная загрузка и отображение названия курса
   */
  it("renders without crashing", async () => {
    (
      getCourseNameModule.getCourseName as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: { name: "Test Course" },
      error: null,
      description: null,
    });
    render(<Templates />);
    await waitFor(() => {
      expect(
        screen.getByText(/Отчеты лабораторных работ курса Test Course/i)
      ).toBeInTheDocument();
    });
  });

  /**
   * Тест проверяет получение и отображение названия курса
   * Проверяется корректность отображения полученного названия в компоненте
   */
  it("fetches and displays course name", async () => {
    (
      getCourseNameModule.getCourseName as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: { name: "Test Course" },
      error: null,
      description: null,
    });
    render(<Templates />);

    await waitFor(() => {
      expect(
        screen.getByText(/Отчеты лабораторных работ курса Test Course/i)
      ).toBeInTheDocument();
    });
  });

  /**
   * Тест проверяет обработку ошибки при получении названия курса
   * При ошибке должен быть редирект на страницу ошибки с соответствующими параметрами
   */
  it("navigates to error page if getCourseName fails", async () => {
    (
      getCourseNameModule.getCourseName as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: null,
      error: 500,
      description: "Internal Server Error",
    });
    render(<Templates />);
    await waitFor(() =>
      expect(mockedNavigate).toHaveBeenCalledWith(
        "/error?code=500&description=Internal Server Error"
      )
    );
  });

  /**
   * Тест проверяет функциональность открытия и закрытия модального окна
   * Проверяется появление и исчезновение модального окна при соответствующих действиях
   */
  it("opens and closes modal", async () => {
    (
      getCourseNameModule.getCourseName as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: { name: "Test Course" },
      error: null,
      description: null,
    });
    render(<Templates />);

    await waitFor(() => {
      expect(
        screen.getByText(/Отчеты лабораторных работ курса Test Course/i)
      ).toBeInTheDocument();
    });

    const openModalButton = screen.getByText("+ Добавить новый шаблон");
    userEvent.click(openModalButton);

    await waitFor(() => {
      expect(screen.getByText(/Шаблон для импорта/i)).toBeInTheDocument();
    });

    const closeModalButton = screen.getByText("×");
    userEvent.click(closeModalButton);
    await waitFor(() =>
      expect(screen.queryByText("Шаблон для импорта")).not.toBeInTheDocument()
    );
  });

  /**
   * Тест проверяет успешную отправку формы и навигацию
   * При успешной загрузке файла должен быть редирект на страницу /template
   */
  it("submits form and navigates to /template on successful upload", async () => {
    (
      getCourseNameModule.getCourseName as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: { name: "Test Course" },
      error: null,
      description: null,
    });
    (
      sendTemplateModule.sendTemplate as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: { some: "data" },
      error: null,
      description: null,
    });
    render(<Templates />);

    await waitFor(() => {
      expect(
        screen.getByText(/Отчеты лабораторных работ курса Test Course/i)
      ).toBeInTheDocument();
    });

    const openModalButton = screen.getByText("+ Добавить новый шаблон");
    userEvent.click(openModalButton);

    await waitFor(() => {
      expect(screen.getByText(/Шаблон для импорта/i)).toBeInTheDocument();
    });

    const fileInput = screen.getByTestId("template");
    const file = new File(["(⌐□_□)"], "chucknorris.png", { type: "image/png" });
    await userEvent.upload(fileInput, file);

    const submitButton = screen.getByText("Загрузить");
    userEvent.click(submitButton);

    expect(sendTemplateModule.sendTemplate).toHaveBeenCalled();
    expect(mockedNavigate).toHaveBeenCalledWith("/template");
  });

  /**
   * Тест проверяет обработку ошибки при загрузке файла
   * При ошибке загрузки должен быть редирект на страницу ошибки
   */
  it("navigates to error page on upload failure", async () => {
    (
      getCourseNameModule.getCourseName as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: { name: "Test Course" },
      error: null,
      description: null,
    });
    (
      sendTemplateModule.sendTemplate as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: null,
      error: 400,
      description: "Bad Request",
    });
    render(<Templates />);

    await waitFor(() => {
      expect(
        screen.getByText(/Отчеты лабораторных работ курса Test Course/i)
      ).toBeInTheDocument();
    });

    const openModalButton = screen.getByText("+ Добавить новый шаблон");
    userEvent.click(openModalButton);

    await waitFor(() => {
      expect(screen.getByText(/Шаблон для импорта/i)).toBeInTheDocument();
    });

    const fileInput = screen.getByTestId(/template/i);
    const file = new File(["(⌐□_□)"], "chucknorris.png", { type: "image/png" });
    await userEvent.upload(fileInput, file);

    const submitButton = screen.getByText("Загрузить");
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(sendTemplateModule.sendTemplate).toHaveBeenCalled();
      expect(mockedNavigate).toHaveBeenCalledWith(
        "/error?code=400&description=Bad Request"
      );
    });
  });

  /**
   * Тест проверяет валидацию формы при отсутствии выбранного файла
   * Форма не должна отправляться, если файл не выбран
   */
  it("does not submit form if no file is selected", async () => {
    (
      getCourseNameModule.getCourseName as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      data: { name: "Test Course" },
      error: null,
      description: null,
    });

    render(<Templates />);
    await waitFor(() => {
      expect(
        screen.getByText(/Отчеты лабораторных работ курса Test Course/i)
      ).toBeInTheDocument();
    });
    const openModalButton = screen.getByText("+ Добавить новый шаблон");
    userEvent.click(openModalButton);

    await waitFor(() => {
      expect(screen.getByText(/Шаблон для импорта/i)).toBeInTheDocument();
    });

    const submitButton = screen.getByText("Загрузить");
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(sendTemplateModule.sendTemplate).not.toHaveBeenCalled();
    });
  });
});
