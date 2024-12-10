import React, { useEffect, useRef, useCallback } from "react";

const Modal = ({ isOpen, onClose, children }) => {
  const modalRef = useRef(null);

  const handleClose = useCallback(
    (event) => {
      if (event.type === "keydown" && event.key !== "Escape") return;
      onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (!isOpen) return;
    document.addEventListener("keydown", handleClose);
    return () => {
      document.removeEventListener("keydown", handleClose);
    };
  }, [isOpen, handleClose]);

  if (!isOpen) return null;

  return (
    <div
      className="p-7 absolute top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 border-solid rounded-2xl border-2 dark:border-zinc-200 border-zinc-950"
      ref={modalRef}
    >
      <div className="mt-5">{children}</div>
      <button
        className="self-start text-3xl absolute top-2 right-5"
        onClick={handleClose}
      >
        &times;
      </button>
    </div>
  );
};

export default Modal;
