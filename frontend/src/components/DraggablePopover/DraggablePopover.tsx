import { useCallback, useEffect, useRef, useState } from "react";

interface DraggablePopoverProps {
  /**
   * Определяет, открыто ли всплывающее окно.
   */
  isOpen: boolean;
  /**
   * Функция обратного вызова для закрытия окна.
   */
  onClose: () => void;
  /**
   * Объект `DOMRect`, представляющий размеры и позицию элемента,
   * относительно которого будет изначально позиционировано всплывающее окно.
   */
  anchorElementRect: DOMRect;
  /**
   * Содержимое всплывающего окна.
   */
  children: React.ReactNode;
}

/**
 * Перетаскиваемое всплывающее окно (popover), которое позиционируется
 * относительно другого элемента на странице.
 *
 * Окно можно закрыть нажатием на крестик или клавишу Escape.
 * Пользователь может перетаскивать окно в пределах границ документа.
 *
 * @component
 * @param {DraggablePopoverProps} props - Свойства компонента.
 * @returns {JSX.Element|null} Перетаскиваемое всплывающее окно или null, если `isOpen` равно `false`.
 */
const DraggablePopover: React.FC<DraggablePopoverProps> = ({
  isOpen,
  onClose,
  anchorElementRect,
  children,
}) => {
  const gap = 10;
  const popoverRef = useRef<HTMLDivElement | null>(null);
  const [position, setPosition] = useState<{ top: number; left: number }>({
    top: 0,
    left: 0,
  });
  const [isPositioned, setIsPositioned] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const mouseOffsetRef = useRef({ x: 0, y: 0 });

  /**
   * Обработчик клика по кнопке закрытия окна.
   */
  const handleCloseClick = useCallback(() => {
    onClose();
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) {
      setIsPositioned(false);
      return;
    }

    /**
     * Обработчик нажатия клавиши для закрытия окна по Escape.
     * @param {KeyboardEvent} event
     */
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen || !popoverRef.current || !anchorElementRect) return;

    const modalHeight = popoverRef.current.offsetHeight;
    const spaceAbove = anchorElementRect.top;
    const x = anchorElementRect.left + window.scrollX;
    const y =
      anchorElementRect.top +
      window.scrollY +
      (spaceAbove >= modalHeight + gap
        ? -1 * (modalHeight + gap)
        : anchorElementRect.height + gap);

    setPosition({
      left: x - anchorElementRect.width / 4,
      top: y,
    });
    setIsPositioned(true);
  }, [isOpen, anchorElementRect]);

  /**
   * Обработчик нажатия кнопки мыши для начала перетаскивания.
   * @param {React.MouseEvent<HTMLDivElement>} event - Событие мыши.
   */
  const handleMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    event.stopPropagation();

    if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      return;
    }

    if (popoverRef.current) {
      const rect = popoverRef.current.getBoundingClientRect();
      mouseOffsetRef.current = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      setIsDragging(true);
    }
  };

  useEffect(() => {
    if (!isDragging) {
      return;
    }

    /**
     * Обработчик перемещения мыши во время перетаскивания.
     * @param {MouseEvent} event
     * @private
     */
    const handleMouseMove = (event: MouseEvent) => {
      if (!popoverRef.current) return;

      const modal = popoverRef.current;
      const modalWidth = modal.offsetWidth;
      const modalHeight = modal.offsetHeight;

      let newLeft = event.clientX - mouseOffsetRef.current.x + window.scrollX;
      let newTop = event.clientY - mouseOffsetRef.current.y + window.scrollY;

      const docMinX = 0,
        docMaxX = document.documentElement.scrollWidth - modalWidth,
        docMinY = 0,
        docMaxY = document.documentElement.scrollHeight - modalHeight;

      newLeft = Math.max(docMinX, Math.min(newLeft, docMaxX));
      newTop = Math.max(docMinY, Math.min(newTop, docMaxY));

      setPosition({
        left: newLeft,
        top: newTop,
      });
    };

    /**
     * Обработчик отпускания кнопки мыши для завершения перетаскивания.
     */
    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    if (popoverRef.current) {
      popoverRef.current.style.cursor = "grabbing";
    }
    const current = popoverRef.current;

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      if (current) {
        current.style.cursor = "grab";
      }
    };
  }, [isDragging]);

  if (!isOpen) return null;

  return (
    <div
      className="dark:bg-zinc-950 bg-zinc-200 p-7 border-solid rounded-2xl border-2 absolute dark:border-zinc-200 border-zinc-950 select-none"
      ref={popoverRef}
      style={{
        left: position.left,
        top: position.top,
        visibility: isPositioned ? "visible" : "hidden",
        cursor: "grab",
        zIndex: 1000,
      }}
      onMouseDown={handleMouseDown}
    >
      <button
        className="self-start text-3xl absolute top-2 right-5"
        onClick={handleCloseClick}
        type="button"
        aria-label="Закрыть"
      >
        &times;
      </button>
      <div className="mt-5">{children}</div>
    </div>
  );
};

export default DraggablePopover;
