import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import Modal from "./Modal";
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("Modal", () => {
  let onCloseMock: () => void;

  beforeEach(() => {
    onCloseMock = vi.fn();
  });

  /**
   * Проверяет, что компонент Modal не рендерится, если свойство isOpen === false.
   * Ожидаемый результат: отсутствует кнопка, закрывающая модальное окно.
   */
  it("no render if modal closed", () => {
    render(<Modal isOpen={false} onClose={onCloseMock} />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  /**
   * Проверяет, что компонент Modal корректно отображает дочерние элементы,
   * если свойство isOpen === true.
   * Ожидаемый результат: содержимое модального окна отображается в DOM.
   */
  it("render with children", () => {
    render(
      <Modal isOpen={true} onClose={onCloseMock}>
        <div>Тестовый контент</div>
      </Modal>
    );

    expect(screen.getByText("Тестовый контент")).toBeInTheDocument();
  });

  /**
   * Проверяет, что функция onClose вызывается при клике на кнопку закрытия.
   * Ожидаемый результат: функция onClose вызывается ровно один раз.
   */
  it("calls onClose close button click", async () => {
    const user = userEvent.setup();
    render(
      <Modal isOpen={true} onClose={onCloseMock}>
        <div>Тестовый контент</div>
      </Modal>
    );

    await user.click(screen.getByRole("button"));
    expect(onCloseMock).toHaveBeenCalledTimes(1);
  });

  /**
   * Проверяет, что функция onClose вызывается при нажатии клавиши Escape.
   * Ожидаемый результат: функция onClose вызывается ровно один раз.
   */
  it("calls onClose on Escape down", async () => {
    const user = userEvent.setup();
    render(
      <Modal isOpen={true} onClose={onCloseMock}>
        <div>Тестовый контент</div>
      </Modal>
    );

    await user.keyboard("{Escape}");
    expect(onCloseMock).toHaveBeenCalledTimes(1);
  });

  /**
   * Проверяет, что функция onClose не вызывается при нажатии других клавиш,
   * кроме Escape (например, Enter, Shift или буква "a").
   * Ожидаемый результат: функция onClose не вызывается.
   */
  it("no calls onClose when downed no-Escape key", async () => {
    const user = userEvent.setup();

    render(
      <Modal isOpen={true} onClose={onCloseMock}>
        <div>Тестовый контент</div>
      </Modal>
    );

    await user.keyboard("{Enter}");
    await user.keyboard("{a}");
    await user.keyboard("{Shift}");
    expect(onCloseMock).not.toHaveBeenCalled();
  });

  /**
   * Проверяет, что функция onClose не вызывается при нажатии клавиши Escape,
   * если модальное окно закрыто (isOpen === false).
   * Ожидаемый результат: функция onClose не вызывается.
   */
  it("no calls onClose in closed and downed Escape", async () => {
    const user = userEvent.setup();
    render(
      <Modal isOpen={false} onClose={onCloseMock}>
        <div>Тестовый контент</div>
      </Modal>
    );

    await user.keyboard("{Escape}");
    expect(onCloseMock).not.toHaveBeenCalled();
  });

  /**
   * Проверяет, что обработчик событий для клавиши Escape добавляется при монтировании
   * компонента и удаляется при размонтировании.
   * Ожидаемый результат:
   * - При монтировании вызывается addEventListener с событием "keydown".
   * - При размонтировании вызывается removeEventListener с событием "keydown".
   */
  it("toggle event listener in mount and unmount", () => {
    const addEventListenerMock = vi.spyOn(document, "addEventListener");
    const removeEventListenerMock = vi.spyOn(document, "removeEventListener");

    const { unmount } = render(<Modal isOpen={true} onClose={onCloseMock} />);

    expect(addEventListenerMock).toHaveBeenCalledWith(
      "keydown",
      expect.any(Function)
    );
    unmount();
    expect(removeEventListenerMock).toHaveBeenCalledWith(
      "keydown",
      expect.any(Function)
    );
  });

  /**
   * Проверяет, что обработчик событий для клавиши Escape не добавляется,
   * если модальное окно закрыто (isOpen === false).
   * Ожидаемый результат: вызова addEventListener с событием "keydown" не происходит.
   */
  it("no escape event listener when modal is close", () => {
    const addEventListenerMock = vi.spyOn(document, "addEventListener");

    render(<Modal isOpen={false} onClose={onCloseMock} />);

    expect(addEventListenerMock).not.toHaveBeenCalledWith(
      "keydown",
      expect.any(Function)
    );
  });
});
