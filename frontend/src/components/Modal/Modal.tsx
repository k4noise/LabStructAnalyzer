import { useEffect, useRef, useCallback } from "react";

/**
 * Компонент модального окна
 *
 * @component
 * @param {Object} props - Свойства компонента.
 * @param {boolean} props.isOpen - Флаг, определяющий, открыто ли модальное окно.
 * @param {Function} props.onClose - Функция, вызываемая при закрытии модального окна.
 * @param {React.ReactNode} props.children - Дочерние элементы, которые отображаются внутри модального окна.
 */
const Modal = ({ isOpen, onClose, children }) => {
  const modalRef = useRef(null);

  /**
   * Обработчик закрытия модального окна.
   *
   * @param {KeyboardEvent|MouseEvent} event - Событие клавиатуры или мыши.
   */
  const handleClose = useCallback(
    (event) => {
      if (event.type === "keydown" && event.key !== "Escape") return;
      onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (!isOpen) return;

    /**
     * Обработчик события нажатия клавиши Escape для закрытия модального окна.
     *
     * @param {KeyboardEvent} event - Событие клавиатуры.
     */
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    document.body.style.paddingRight = `
      ${window.innerWidth - document.documentElement.clientWidth}px`;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);

      document.body.style.overflow = "visible";
      document.body.style.paddingRight = "0";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="dark:bg-zinc-950 bg-zinc-200 p-7 fixed top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 border-solid rounded-2xl border-2 dark:border-zinc-200 border-zinc-950"
      ref={modalRef}
    >
      <button
        className="self-start text-3xl absolute top-2 right-5"
        onClick={handleClose}
      >
        &times;
      </button>
      <div className="mt-5">{children}</div>
    </div>
  );
};

export default Modal;
